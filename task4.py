import sys
import math
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from collections import deque
import numpy as np

# ----- CONFIG -----
PORT = 'COM20'  # Adjust as needed
BAUD = 230400
WINDOW = 200
UPDATE_INTERVAL = 20  # ms (~50 Hz)
ser = serial.Serial(PORT, BAUD, timeout=0.1)

pitch_buf = deque(maxlen=WINDOW)
roll_buf  = deque(maxlen=WINDOW)
yaw_buf   = deque(maxlen=WINDOW)
x_idx     = deque(maxlen=WINDOW)

fig = plt.figure(figsize=(14, 6))

# Left: time-series
ax1 = fig.add_subplot(1, 2, 1)
line_pitch, = ax1.plot([], [], label="Pitch (°)", color='tab:blue', linewidth=2)
line_roll,  = ax1.plot([], [], label="Roll (°)", color='tab:orange', linewidth=2)
line_yaw,   = ax1.plot([], [], label="Yaw (°)", color='tab:green', linewidth=2)
ax1.set_xlim(0, WINDOW)
ax1.set_ylim(-180, 180)
ax1.set_xlabel("Samples")
ax1.set_ylabel("Angle (°)")
ax1.set_title("MPU6050 Pitch, Roll, Yaw")
ax1.legend(loc="upper right")
ax1.grid(True, alpha=0.3)
ax1.axhline(y=0, color='k', linestyle='--', alpha=0.3)

# Right: 3D gun
ax2 = fig.add_subplot(1, 2, 2, projection='3d')
ax2.set_xlim(-1, 1)
ax2.set_ylim(-1, 1)
ax2.set_zlim(-1, 1)
ax2.set_xlabel('X (Roll axis)')
ax2.set_ylabel('Y (Pitch axis)')
ax2.set_zlabel('Z (Up)')
ax2.set_title("3D Gun - Black")
ax2.view_init(elev=20, azim=45)

# ----- Gun model -----
def box(cx, cy, cz, sx, sy, sz):
    return np.array([
        [cx - sx, cy - sy, cz - sz],
        [cx + sx, cy - sy, cz - sz],
        [cx + sx, cy + sy, cz - sz],
        [cx - sx, cy + sy, cz - sz],
        [cx - sx, cy - sy, cz + sz],
        [cx + sx, cy - sy, cz + sz],
        [cx + sx, cy + sy, cz + sz],
        [cx - sx, cy + sy, cz + sz],
    ])

def faces_from_box(v):
    idx = [[0,1,2,3],[4,5,6,7],[0,1,5,4],
           [1,2,6,5],[2,3,7,6],[3,0,4,7]]
    return [v[i] for i in idx]

# Define gun parts
boxes = [
    box(0.15, 0, 0.05, 0.45, 0.08, 0.06),  # slide
    box(0.60, 0, 0.05, 0.12, 0.035, 0.03), # barrel
    box(-0.28, 0, -0.2, 0.12, 0.07, 0.2),  # grip
    box(-0.05, -0.08, -0.02, 0.08, 0.03, 0.04) # guard
]

vertices = np.vstack(boxes)
face_indices = []
offset = 0
for b in boxes:
    face_indices.extend([[offset+i for i in f] for f in [[0,1,2,3],[4,5,6,7],
                                                        [0,1,5,4],[1,2,6,5],
                                                        [2,3,7,6],[3,0,4,7]]])
    offset += 8

poly = Poly3DCollection([vertices[f] for f in face_indices], facecolors='black', edgecolors='k', linewidths=0.2)
ax2.add_collection3d(poly)

# ----- Rotation -----
def rotation_matrix(pitch, roll, yaw):
    p, r, y = map(np.radians, [pitch, roll, yaw])
    Rx = np.array([[1,0,0],[0,np.cos(r),-np.sin(r)],[0,np.sin(r),np.cos(r)]])
    Ry = np.array([[np.cos(p),0,np.sin(p)],[0,1,0],[-np.sin(p),0,np.cos(p)]])
    Rz = np.array([[np.cos(y),-np.sin(y),0],[np.sin(y),np.cos(y),0],[0,0,1]])
    return Rz @ Ry @ Rx

def rotate_vertices(verts, R):
    return (R @ verts.T).T

def update_3d_gun(pitch, roll, yaw):
    R = rotation_matrix(pitch, roll, yaw)
    rotated = rotate_vertices(vertices, R)
    new_faces = [rotated[f] for f in face_indices]
    poly.set_verts(new_faces)

# ----- Parsing -----
def parse_line(line):
    try:
        parts = line.strip().split(',')
        if len(parts) >= 3:
            return float(parts[0]), float(parts[1]), float(parts[2])
    except:
        pass
    return None, None, None

# ----- Animation -----
def init():
    line_pitch.set_data([], [])
    line_roll.set_data([], [])
    line_yaw.set_data([], [])
    update_3d_gun(0,0,0)
    return (line_pitch, line_roll, line_yaw, poly)

def update(frame):
    lines = []
    for _ in range(20):
        raw = ser.readline().decode(errors='ignore')
        if not raw:
            break
        lines.append(raw)
    for raw in lines:
        pitch, roll, yaw = parse_line(raw)
        if pitch is None:
            continue
        pitch_buf.append(pitch)
        roll_buf.append(roll)
        yaw_buf.append(yaw)
        x_idx.append(len(x_idx)+1 if x_idx else 1)
    # Update lines
    xs = list(range(len(x_idx)))
    line_pitch.set_data(xs, list(pitch_buf))
    line_roll.set_data(xs, list(roll_buf))
    line_yaw.set_data(xs, list(yaw_buf))
    ax1.set_xlim(max(0,len(xs)-WINDOW), max(WINDOW,len(xs)))
    # Update 3D gun
    if pitch_buf:
        update_3d_gun(pitch_buf[-1], roll_buf[-1], yaw_buf[-1])
    return (line_pitch, line_roll, line_yaw, poly)

ani = animation.FuncAnimation(fig, update, init_func=init, interval=UPDATE_INTERVAL, blit=False)
plt.tight_layout()
plt.show()
