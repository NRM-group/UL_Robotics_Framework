import sys
import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.image as image
from matplotlib.offsetbox import OffsetImage, AnchoredOffsetbox



# Example trajectory (a square path for demonstration)
trajectory = [
    (0, 0), (1, 0), (2, 0), (3, 0),
    (3, 1), (3, 2), (3, 3),
    (2, 3), (1, 3), (0, 3),
    (0, 2), (0, 1), (0, 0)
]


# Duplicate for smooth looping
trajectory = trajectory * 10  

# Parameters
radius_circle = 1  

#Setup for image of the ghost title
im = image.imread('ghostnoback.png')

def place_image(im, loc=3, ax=None, zoom=1, **kw):
    if ax==None: ax=plt.gca()
    imagebox = OffsetImage(im, zoom=zoom*0.72)
    ab = AnchoredOffsetbox(loc=loc, child=imagebox, frameon=False, **kw)
    ax.add_artist(ab)

#Flip Image
im_flipped = np.fliplr(im)

########################################Non-transparent Work##########################

""" 


# Setup figure
fig, ax = plt.subplots()
ax.set_aspect('equal')
ax.set_xlim(-60, 60)
ax.set_ylim(-30, 30)
fig.patch.set_alpha(0.0)
ax.set_facecolor("none")
ax.axis("off")


place_image(im_flipped, loc='lower right', pad=0, zoom=.15)


# Create two circles
circle1 = plt.Circle(trajectory[0], radius_circle, color='blue')
circle2 = plt.Circle(trajectory[0], radius_circle, color='red')
ax.add_patch(circle1)
ax.add_patch(circle2)

# Update function for animation
def update(frame):
    # Wrap around trajectory
    idx1 = frame % len(trajectory)
    idx2 = (frame + len(trajectory)//2) % len(trajectory)  # offset second circle
    
    # Move circles
    circle1.center = trajectory[idx1]
    circle2.center = trajectory[idx2]
    
    return circle1, circle2

# Animate
ani = FuncAnimation(fig, update, frames=np.arange(0, len(trajectory)), interval=200, blit=True)
plt.show()
"""

################Transparent Window#################################

class TransparentWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Try to make the window itself translucent & frameless
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # Create a container widget (transparent)
        container = QtWidgets.QWidget()
        container.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        container.setStyleSheet("background:transparent;")
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure + axes
        self.fig, self.ax = plt.subplots()
        # Make sure the figure and axes are fully transparent
        self.fig.patch.set_alpha(0.0)
        self.fig.patch.set_facecolor((0, 0, 0, 0))
        self.ax.set_facecolor((0, 0, 0, 0))
        self.ax.axis("off")

        # Aspect & limits (your values)
        self.ax.set_aspect("equal")
        self.ax.set_xlim(-60, 60)
        self.ax.set_ylim(-30, 30)

        # Add image (anchored)
        place_image(im_flipped, loc='lower right', pad=0, zoom=0.15, ax=self.ax)

        # Circles (zorder high so they appear above image if needed)
        self.circle1 = plt.Circle(trajectory[0], radius_circle, color='blue', zorder=5)
        self.circle2 = plt.Circle(trajectory[0], radius_circle, color='red', zorder=5)
        self.ax.add_patch(self.circle1)
        self.ax.add_patch(self.circle2)

        # Canvas: ensure it is transparent at the QWidget level
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.canvas.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.canvas.setStyleSheet("background:transparent;")
        # Prevent Qt from filling background
        self.canvas.setAutoFillBackground(False)

        layout.addWidget(self.canvas)
        self.setCentralWidget(container)

        # Animation using QTimer (more reliable with Qt than FuncAnimation/blitting)
        self._frame = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(200)   # interval ms (same as your original)

    def advance(self):
        idx1 = self._frame % len(trajectory)
        idx2 = (self._frame + len(trajectory)//2) % len(trajectory)
        self.circle1.center = trajectory[idx1]
        self.circle2.center = trajectory[idx2]
        self._frame += 1
        # draw only when needed
        self.canvas.draw_idle()

# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    w = TransparentWindow()
    # Try both: windowed first (for debugging). Change to showFullScreen() for projection.
    w.show()             # try this first -- if it looks transparent, then:
    # w.showFullScreen()  # use this for final projection

    sys.exit(app.exec_())