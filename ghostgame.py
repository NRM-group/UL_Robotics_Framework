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

#BLUE SPHERE
trajectory = [
    (0, 0), (100, 0), (200, 0), (300, 0),
    (300, 10), (200, 20), (100, 20),
    (100, 30), (200, 35), (300, 40),
    (200, 40), (100, 45), (0, 50)
]

#RED SPHERE

trajectory2 = [
    (30,0),(0, 20), (0, 10), (0, 0),
    (20, 30), (10, 30), (0, 30),
    (30, 10), (30, 20), (30, 30),(0, 0),
    (10, 0), (20, 0), (30, 0)
]




# Duplicate for smooth looping
trajectory = trajectory * 10 
trajectory2 = trajectory2 * 10  

# Parameters
radius_circle = 10 

#Setup for image of the ghost title
im = image.imread('/home/alejandrohernandez/Desktop/TherapyRepo-main/ghostnoback.png')

def place_image(im, loc=9, ax=None, zoom=1, **kw):
    if ax==None: ax=plt.gca()
    imagebox = OffsetImage(im_flipped2, zoom=zoom*0.72)
    ab = AnchoredOffsetbox(loc=loc, child=imagebox, frameon=False, **kw)
    ax.add_artist(ab)

#Flip Image left-right
im_flipped = np.fliplr(im)

#Flip Image 
im_flipped2 = np.flipud(im)

########################################Non-transparent Work##########################

""" 

    def advance(self):

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
        container.setStyleSheet("background:black;")
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
        self.ax.set_xlim(-1280, 1280)
        self.ax.set_ylim(-900, 900)

        # Add image (anchored)
        place_image(im, loc='upper right', pad=0, zoom=0.15, ax=self.ax)

        # Circles (zorder high so they appear above image if needed)
        self.circle1 = plt.Circle(trajectory[0], radius_circle, color='blue', zorder=5)
        self.circle2 = plt.Circle(trajectory2[0], radius_circle, color='red', zorder=5)
        self.ax.add_patch(self.circle1)
        self.ax.add_patch(self.circle2)

        # Canvas: ensure it is transparent at the QWidget level
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.canvas.setAttribute(QtCore.Qt.WA_NoSystemBackground, True)
        self.canvas.setStyleSheet("background:black;")
        # Prevent Qt from filling background
        self.canvas.setAutoFillBackground(False)

        layout.addWidget(self.canvas)
        self.setCentralWidget(container)


############# PROGRAM WITH PRE-SELECTED CIRCLES ##################

    #     # Animation using QTimer (more reliable with Qt than FuncAnimation/blitting)
    #     self._frame = 0
    #     self.timer = QtCore.QTimer(self)
    #     self.timer.timeout.connect(self.advance)
    #     self.timer.start(200)   # interval ms (same as your original)




    # def advance(self):
    #     idx1 = self._frame % len(trajectory)
    #     self.circle1.center = trajectory[idx1]
    #     self.circle2.center = trajectory2[idx1]
    #     self._frame += 1
    #     # draw only when needed
    #     self.canvas.draw_idle()

#################### PROGRAM WITH MOUSE FOLLOWING ###############


        # Animation
        self._frame = 0
        self.target_index = 0
        self.mouse_x, self.mouse_y = 0, 0
        self.threshold = 25  # distance threshold for "meeting point"

        # Track mouse movement
        self.canvas.setMouseTracking(True)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        # Timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(50)  # ms

    def on_mouse_move(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.mouse_x = event.xdata
            self.mouse_y = event.ydata
            # Move red circle (follows mouse)
            self.circle2.center = (self.mouse_x, self.mouse_y)

    def advance(self):
        # Get current target for blue circle
        if self.target_index >= len(trajectory):
            self.target_index = 0

        target_x, target_y = trajectory[self.target_index]
        curr_x, curr_y = self.circle1.center

        # Compute distance from red circle (mouse)
        dist_to_red = np.hypot(self.mouse_x - target_x, self.mouse_y - target_y)

        # Blue waits until red (mouse) gets close to its current target
        if dist_to_red < self.threshold:
            # Move blue to the next point
            self.target_index += 1
            if self.target_index < len(trajectory):
                self.circle1.center = trajectory[self.target_index]

        self.canvas.draw_idle()

#ROS VERSION


    
#    def lookup_tf_position(self):

#        try:
#            (trans, rot) = self.tf_listener.lookupTransform(
#                self.frame_a, self.frame_b, rospy.Time(0)
#            )
#            x, y, z = trans
#            return np.array([x * 1000, y * 1000])
#        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
#            return None


# ---------------------------
# Run the app
# ---------------------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = TransparentWindow()
    # Try both: windowed first (for debugging). Change to showFullScreen() for projection.
    #w.show()             # try this first -- if it looks transparent, then:
    w.showFullScreen()  # use this for final projection

    sys.exit(app.exec_())