import serial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

PORT = 'COM20'
BAUD = 230400
ser = serial.Serial(PORT, BAUD, timeout=0.1)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-1,1])
ax.set_ylim([-1,1])
ax.set_zlim([-1,1])
ax.set_xlabel("Roll")
ax.set_ylabel("Pitch")
ax.set_zlabel("Z axis")
ax.set_title("Pitch + Roll 3D")

# Simple cube
cube = np.array([[0,0,0],[0.2,0,0],[0.2,0.2,0],[0,0.2,0],
                 [0,0,0.2],[0.2,0,0.2],[0.2,0.2,0.2],[0,0.2,0.2]])
faces = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
poly = Poly3DCollection([cube[f] for f in faces], facecolors='cyan', edgecolors='k', linewidths=1)
ax.add_collection3d(poly)

def rotation_matrix(pitch, roll):
    p = np.radians(pitch)
    r = np.radians(roll)
    Rx = np.array([[1,0,0],[0,np.cos(r),-np.sin(r)],[0,np.sin(r),np.cos(r)]])
    Ry = np.array([[np.cos(p),0,np.sin(p)],[0,1,0],[-np.sin(p),0,np.cos(p)]])
    return Ry @ Rx

def rotate_cube(pitch, roll):
    R = rotation_matrix(pitch, roll)
    rotated = (R @ cube.T).T
    poly.set_verts([rotated[f] for f in faces])
    plt.draw()
    plt.pause(0.01)

while True:
    raw = ser.readline().decode(errors='ignore')
    if raw.strip() == "":
        continue
    try:
        pitch, roll = map(float, raw.strip().split(',')[:2])  # only pitch & roll
    except:
        continue
    rotate_cube(pitch, roll)
