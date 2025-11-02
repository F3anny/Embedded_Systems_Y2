import sys
import math
import random
import time
import threading
import re
from collections import deque

try:
    import pygame
except ImportError:
    print("Install pygame: pip install pygame")
    sys.exit(1)

try:
    import serial
    import serial.tools.list_ports
    import numpy as np
except Exception:
    serial = None

SCREEN_W, SCREEN_H = 900, 700

# --- Simple MPU Reader ---
class SimpleMPU:
    def __init__(self, baudrate=115200, timeout=0.05):
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False
        self.running = False
        self.history = deque(maxlen=8)
        self._lock = threading.Lock()

    def scan_and_connect(self):
        if serial is None:
            return False
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            try:
                s = serial.Serial(p.device, baudrate=self.baudrate, timeout=self.timeout)
                time.sleep(0.05)
                for _ in range(4):
                    ln = s.readline().decode(errors='ignore')
                    if "Gyro" in ln or "Accel" in ln:
                        self.ser = s
                        self.connected = True
                        print("MPU connected on", p.device)
                        return True
                s.close()
            except Exception:
                continue
        return False

    def start(self):
        if not self.connected:
            return False
        self.running = True
        self.t = threading.Thread(target=self.loop, daemon=True)
        self.t.start()
        return True

    def stop(self):
        self.running = False
        if hasattr(self, 't') and self.t.is_alive():
            self.t.join(timeout=0.3)
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        self.connected = False

    def loop(self):
        while self.running and self.ser:
            try:
                ln = self.ser.readline().decode(errors='ignore').strip()
                if not ln:
                    continue
                parts = ln.split("|")
                accel = parts[0] if parts else ""
                matches = re.findall(r"([XYZ]):(-?\d+\.?\d*)", accel)
                ax = ay = 0.0
                for axis, v in matches:
                    if axis == 'X': ax = float(v)
                    if axis == 'Y': ay = float(v)
                with self._lock:
                    self.history.append((ax, ay))
                time.sleep(0.01)
            except Exception:
                time.sleep(0.01)

    def get(self):
        if not self.connected:
            return 0.0, 0.0
        with self._lock:
            if not self.history:
                return 0.0, 0.0
            arr = np.array(self.history)
            w = np.linspace(0.4, 1.0, arr.shape[0])
            w /= w.sum()
            avg = np.average(arr, axis=0, weights=w)
            return float(avg[0]) * 1.8, float(avg[1]) * 1.8

# --- Player ---
class Player:
    def __init__(self):
        self.pos = pygame.Vector2(SCREEN_W/2, SCREEN_H/2)
        self.vel = pygame.Vector2(0,0)
        self.radius = 18
        self.color = (140, 100, 255)
        self.boost_cd = 1.2
        self.last_boost = -10.0

    def update(self, inp_x, inp_y, dt, now):
        acc = pygame.Vector2(inp_x, inp_y) * 450.0
        self.vel += acc * dt
        self.vel *= 0.995
        if self.vel.length() > 650:
            self.vel.scale_to_length(650)
        self.pos += self.vel * dt
        # Wrap around edges for smooth zero-G motion
        if self.pos.x < -50: self.pos.x = SCREEN_W + 50
        if self.pos.x > SCREEN_W + 50: self.pos.x = -50
        if self.pos.y < -50: self.pos.y = SCREEN_H + 50
        if self.pos.y > SCREEN_H + 50: self.pos.y = -50

    def boost(self, now):
        if now - self.last_boost >= self.boost_cd:
            self.last_boost = now
            if self.vel.length() < 30:
                angle = random.random()*math.tau
                self.vel += pygame.Vector2(math.cos(angle), math.sin(angle)) * 320
            else:
                self.vel += self.vel.normalize() * 420
            return True
        return False

    def draw(self, surf):
        # Player glow
        glow_color = (180, 120, 255)
        pygame.draw.circle(surf, glow_color, self.pos, self.radius + 4)
        pygame.draw.circle(surf, self.color, self.pos, self.radius)
        # Trail
        if self.vel.length() > 10:
            tail = -self.vel.normalize() * 20
            pygame.draw.line(surf, (200,180,255), self.pos, (self.pos + tail), 3)

# --- Asteroids ---
class Asteroid:
    def __init__(self):
        side = random.choice(['top','left','right','bottom'])
        pad = 40
        if side == 'top':
            self.pos = pygame.Vector2(random.uniform(0, SCREEN_W), -pad)
            self.vel = pygame.Vector2(random.uniform(-120, 120), random.uniform(80, 240))
        elif side == 'bottom':
            self.pos = pygame.Vector2(random.uniform(0, SCREEN_W), SCREEN_H + pad)
            self.vel = pygame.Vector2(random.uniform(-120, 120), random.uniform(-240, -80))
        elif side == 'left':
            self.pos = pygame.Vector2(-pad, random.uniform(0, SCREEN_H))
            self.vel = pygame.Vector2(random.uniform(80, 240), random.uniform(-120,120))
        else:
            self.pos = pygame.Vector2(SCREEN_W + pad, random.uniform(0, SCREEN_H))
            self.vel = pygame.Vector2(random.uniform(-240, -80), random.uniform(-120,120))
        self.size = random.uniform(14, 52)
        self.spin = random.uniform(-90, 90)
        self.angle = random.uniform(0, 360)
        self.color = (220, 190, 255)

    def update(self, dt):
        self.pos += self.vel * dt
        self.angle += self.spin * dt

    def draw(self, surf):
        r = int(self.size)
        rect = pygame.Rect(0,0, r*2, r*2)
        rect.center = self.pos
        pygame.draw.ellipse(surf, self.color, rect)

# --- Main Game ---
def run_game(port_hint=None):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("🌌 NovaDash")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas', 20)

    mpu = SimpleMPU()
    if serial is not None:
        try:
            if port_hint:
                mpu.ser = serial.Serial(port_hint, baudrate=115200, timeout=0.05)
                mpu.connected = True
                mpu.start()
            else:
                mpu.scan_and_connect()
                if mpu.connected:
                    mpu.start()
        except Exception:
            mpu.connected = False

    player = Player()
    asteroids = []
    spawn_timer = 0.0
    spawn_interval = 1.1
    score = 0
    running = True
    start_time = time.time()

    while running:
        dt = clock.tick(60) / 1000.0
        now = time.time()
        inp_x = inp_y = 0.0
        keys = pygame.key.get_pressed()
        if mpu.connected:
            ax, ay = mpu.get()
            inp_x = -ax
            inp_y = ay
            inp_x = max(-1.0, min(1.0, inp_x))
            inp_y = max(-1.0, min(1.0, inp_y))
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: inp_x = -1.0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: inp_x = 1.0
            if keys[pygame.K_UP] or keys[pygame.K_w]: inp_y = -1.0
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: inp_y = 1.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    player.boost(now)
                if ev.key == pygame.K_ESCAPE:
                    running = False

        elapsed = now - start_time
        spawn_interval = max(0.32, 1.1 - elapsed * 0.01)
        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0.0
            asteroids.append(Asteroid())

        player.update(inp_x, inp_y, dt, now)
        for a in asteroids:
            a.update(dt)

        to_remove = []
        for a in asteroids:
            if (a.pos - player.pos).length() < (a.size + player.radius)*0.8:
                running = False
            if a.pos.x < -200 or a.pos.x > SCREEN_W + 200 or a.pos.y < -200 or a.pos.y > SCREEN_H + 200:
                to_remove.append(a)
                score += 1
        for r in to_remove:
            try: asteroids.remove(r)
            except: pass

        # Draw cosmic theme
        screen.fill((15, 10, 35))
        for i in range(80):
            x = (i * 59) % SCREEN_W
            y = ((i * 77) + int(now*40)) % SCREEN_H
            pygame.draw.circle(screen, (40, 30, 80), (x,y), 1)

        for a in asteroids:
            a.draw(screen)
        player.draw(screen)

        s_surf = font.render(f"✨ Score: {score}", True, (255,255,255))
        t_surf = font.render(f"⏱ Time: {int(elapsed)}s", True, (200,200,255))
        mpu_surf = font.render("🎮 MPU: Connected" if mpu.connected else "⌨ Keyboard Mode", True, (180,220,255))
        screen.blit(s_surf, (12,12))
        screen.blit(t_surf, (12,36))
        screen.blit(mpu_surf, (12,60))
        pygame.display.flip()

    if mpu.connected:
        mpu.stop()
    show_gameover(screen, score)
    pygame.quit()

def show_gameover(screen, score):
    font = pygame.font.SysFont('consolas', 50)
    small = pygame.font.SysFont('consolas', 22)
    clock = pygame.time.Clock()
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or ev.type == pygame.KEYDOWN:
                return
        screen.fill((10, 5, 25))
        txt = font.render("💀 GAME OVER 💀", True, (230,100,255))
        sc = small.render(f"Score: {score}   Press any key to exit", True, (220,220,255))
        screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 70))
        screen.blit(sc, (SCREEN_W//2 - sc.get_width()//2, SCREEN_H//2 + 10))
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    port = None
    if len(sys.argv) > 1:
        port = sys.argv[1]
    run_game(port)
