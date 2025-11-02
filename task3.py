import serial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from collections import deque
import numpy as np

# ----- CONFIG -----
PORT = 'COM20'
BAUD = 230400
WINDOW = 200

ser = serial.Serial(PORT, BAUD, timeout=0.1)

pitch_buf = deque(maxlen=WINDOW)
roll_buf = deque(maxlen=WINDOW)
x_idx = deque(maxlen=WINDOW)

fig = plt.figure(figsize=(10,6))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_zlim(-1, 1)
ax.set_xlabel('Roll axis')
ax.set_ylabel('Pitch axis')
ax.set_zlabel('Up')
ax.set_title("3D Pitch & Roll Visualization")

# Define a simple flat rectangle to represent orientation
verts = np.array([
    [-0.5, -0.1, 0],
    [0.5, -0.1, 0],
    [0.5, 0.1, 0],
    [-0.5, 0.1, 0]
])
rect = ax.plot([0,0],[0,0],[0,0])[0]

def rotation_matrix(pitch, roll):
    p = np.radians(pitch)
    r = np.radians(roll)
    Rx = np.array([[1,0,0],[0,np.cos(r),-np.sin(r)],[0,np.sin(r),np.cos(r)]])
    Ry = np.array([[np.cos(p),0,np.sin(p)],[0,1,0],[-np.sin(p),0,np.cos(p)]])
    return Ry @ Rx

def update_rect(pitch, roll):
    R = rotation_matrix(pitch, roll)
    rotated = (R @ verts.T).T
    ax.collections.clear()
    ax.add_collection3d(plt.Poly3DCollection([rotated], facecolors='cyan', edgecolors='k', linewidths=1))

while True:
    raw = ser.readline().decode(errors='ignore')
    try:
        pitch, roll, yaw = map(float, raw.strip().split(','))
    except:
        continue
    
    pitch_buf.append(pitch)
    roll_buf.append(roll)
    x_idx.append(len(x_idx)+1 if x_idx else 1)
    
    if pitch_buf:
        update_rect(pitch_buf[-1], roll_buf[-1])
    plt.pause(0.01)
