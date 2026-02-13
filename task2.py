import serial
import matplotlib.pyplot as plt
from collections import deque

# ----- CONFIG -----
PORT = 'COM20'  # Change to your Arduino port
BAUD = 230400
WINDOW = 200

ser = serial.Serial(PORT, BAUD, timeout=0.1)

pitch_buf = deque(maxlen=WINDOW)
x_idx = deque(maxlen=WINDOW)

plt.ion()
fig, ax = plt.subplots(figsize=(10, 5))
line_pitch, = ax.plot([], [], label="Pitch (°)", color='tab:blue', linewidth=2)
ax.set_xlim(0, WINDOW)
ax.set_ylim(-180, 180)
ax.set_xlabel("Samples")
ax.set_ylabel("Pitch (°)")
ax.set_title("MPU6050 Pitch Only")
ax.grid(True)
ax.legend()

while True:
    raw = ser.readline().decode(errors='ignore')
    try:
        pitch, roll, yaw = map(float, raw.strip().split(','))
    except:
        continue
    
    pitch_buf.append(pitch)
    x_idx.append(len(x_idx)+1 if x_idx else 1)
    
    # Update plot
    line_pitch.set_data(range(len(x_idx)), list(pitch_buf))
    ax.set_xlim(max(0,len(x_idx)-WINDOW), max(WINDOW,len(x_idx)))
    plt.pause(0.01)
