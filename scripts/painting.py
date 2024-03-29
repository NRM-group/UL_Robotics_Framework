#!/usr/bin/env python3
import rospy
import sys
import tf2_ros
import tf2_geometry_msgs.tf2_geometry_msgs
import message_filters
import numpy as np
from std_msgs.msg import String, Int8, ColorRGBA
from geometry_msgs.msg import PointStamped, PoseStamped, Point, WrenchStamped
from dynamic_reconfigure.msg import Config, DoubleParameter, GroupState
from std_msgs.msg import Int16MultiArray
from sensor_msgs.msg import JointState
from visualization_msgs.msg import MarkerArray, Marker
from franka_msgs.msg import FrankaState
import tf.transformations as tr
from panda_ros.msg import ImpedanceParams, StiffnessConfig
from copy import deepcopy
from analytics.analytics_config import *

class paint_publisher:
	"""
	Class that handles visualising the cubic workspace 
	"""

	def __init__(self):
		self.sub = rospy.Subscriber("/franka_state_controller/franka_states", FrankaState, self.paint)
		self.pub = rospy.Publisher("/cartesian_impedance_equilibrium_controller/painting", Marker, queue_size=5)
		self.workspace_pub = rospy.Publisher("/cartesian_impedance_equilibrium_controller/robot_workspace_approx", Marker, queue_size=5)
		self.unity_pub = rospy.Publisher("/unity/painting", JointState, queue_size=5)

		self.robot_pose_eq = PoseStamped()
		self.robot_pose = PoseStamped()
		
		self.robot_pose_list = []

		self.robot_pose.header.frame_id = "panda_link0"

		# Used for colouring
		self.f_max_observable = 30

		
		self.pos_marker = Marker()

		# Resolution of cube (10^(-cube_res))
		self.cube_res_places = 2
		self.cube_res_factor = 5
		self.cube_res = self.cube_res_factor * 10**(-self.cube_res_places)

		# Side width of cube workspace (meters) (min is 2x max reach of robot)
		self.cube_len = 4
		self.cube_grid = np.zeros((int(self.cube_len/self.cube_res), int(self.cube_len/self.cube_res), int(self.cube_len/self.cube_res)), dtype=np.bool8)
		self.value_grid = np.zeros((int(self.cube_len/self.cube_res), int(self.cube_len/self.cube_res), int(self.cube_len/self.cube_res)), dtype=np.float32)
		
		# Unique Marker ID
		self.idx = 0



	def paint(self, state: FrankaState):
		"""
		Callback for painting when receiving a franka state message

		Args:
			state (FrankaState): current state of the panda
		"""
		self.init_marker()
		self.generate_workspace_marker()
		self.generate_marker(state)

	def init_marker(self):
		"""
		Convenience function to initialise a marker for visualisation of cubes
		"""
		self.pos_marker.id = self.idx
		self.pos_marker.header.frame_id = self.robot_pose.header.frame_id
		self.pos_marker.pose.orientation.x = 0
		self.pos_marker.pose.orientation.y = 0
		self.pos_marker.pose.orientation.z = 0
		self.pos_marker.pose.orientation.w = 1
		self.pos_marker.color.a = 1
		self.pos_marker.color.r = 1.0
		self.pos_marker.color.g = 0.0
		self.pos_marker.color.b = 0.0
		self.pos_marker.type = Marker.CUBE_LIST
		self.pos_marker.header.stamp = rospy.Time.now()
		self.pos_marker.scale.x = self.cube_res
		self.pos_marker.scale.y = self.cube_res
		self.pos_marker.scale.z = self.cube_res

	def generate_workspace_marker(self):
		"""
		Generate a marker representing the approximate workspace of the panda
		"""
		self.workspace_marker = Marker()
		self.workspace_marker.id = self.idx
		# self.idx += 1
		self.workspace_marker.header.frame_id = self.robot_pose.header.frame_id
		self.workspace_marker.pose.position.x = 0
		self.workspace_marker.pose.position.y = 0
		self.workspace_marker.pose.position.z = 0

		self.workspace_marker.pose.orientation.x = 0
		self.workspace_marker.pose.orientation.y = 0
		self.workspace_marker.pose.orientation.z = 0
		self.workspace_marker.pose.orientation.w = 1
		self.workspace_marker.color.a = 0.01
		self.workspace_marker.color.r = 1.0
		self.workspace_marker.color.g = 1.0
		self.workspace_marker.color.b = 1.0
		self.workspace_marker.type = Marker.SPHERE
		self.workspace_marker.header.stamp = rospy.Time.now()
		self.workspace_marker.scale.x = 1
		self.workspace_marker.scale.y = 1
		self.workspace_marker.scale.z = 1
		
		self.workspace_pub.publish(self.workspace_marker)




	def generate_marker(self, state: FrankaState):
		"""
		Generates a marker at the current position of the panda end effector

		Args:
			state (FrankaState): Current state of the panda
		"""
		wrench_o = state.O_F_ext_hat_K
		f_vec = np.array([wrench_o[0], wrench_o[1], wrench_o[2]])
		
		# Get Force and torque magnitude
		f_mag = np.linalg.norm(f_vec)-4

		x, y, z = self.snap_grid(state.O_T_EE[12], state.O_T_EE[13], state.O_T_EE[14])

		taken = self.update_point(x, y, z, f_mag)
		if taken:
			return

		# # Uncomment to log cubes for analysis later - warning - it might cause lagging. This should eb optimised in the future
		# nz = np.nonzero(self.value_grid)
		# np.savetxt(cubic_coord_pipe, nz)
		# ls = []
		# for i in range(len(nz[0])):
		# 	ls.append(self.value_grid[nz[0][i], nz[1][i], nz[2][i]])
		# np.savetxt(cubic_value_pipe, np.array(ls))
		
		point = Point()
		point.x = x
		point.y = y
		point.z = z

		
		rg_ratio = f_mag/self.f_max_observable

		if rg_ratio < 0:
			rg_ratio = 0
		elif rg_ratio > 1:
			rg_ratio = 1

		colour = ColorRGBA()
		colour.a = 0.5
		colour.r = (1 - rg_ratio) #* 127
		colour.g = rg_ratio #* 127
		colour.b = 0

		self.pos_marker.points.append(point)
		self.pos_marker.colors.append(colour)

		self.pub_to_unity(x, y, z, colour.a, colour.r, colour.g, colour.b, wrench_o)
		self.pub.publish(self.pos_marker)

	def update_point(self, x, y, z, f_mag):
		"""
		Update 

		Args:
			x (_type_): _description_
			y (_type_): _description_
			z (_type_): _description_
			f_mag (_type_): _description_

		Returns:
			_type_: _description_
		"""
		cube_grid_index_offset = self.cube_len/2
		x, y, z = int((cube_grid_index_offset + x)/self.cube_res), int((cube_grid_index_offset + y)/self.cube_res), int((cube_grid_index_offset + z)/self.cube_res)
		
		if self.value_grid[x-1,y-1,z-1] < f_mag:
			self.value_grid[x-1,y-1,z-1] = f_mag
			return False
		return True

	def check_point(self, x, y, z):
		"""
		Check if the current coordinates have been occupied before

		Args:
			x (int): x coordinate of point
			y (int): y coordinate of point
			z (int): z coordinate of point

		Returns:
			boolean: Boolean representing whether the coordinate has been occupied before
		"""
		cube_grid_index_offset = self.cube_len/2
		x, y, z = int((cube_grid_index_offset + x)/self.cube_res), int((cube_grid_index_offset + y)/self.cube_res), int((cube_grid_index_offset + z)/self.cube_res)
		
		if not self.cube_grid[x-1,y-1,z-1]:
			self.cube_grid[x,y,z] = 1
			return False
		return True
	
	def pub_to_unity(self, x, y, z, a, r, g, b, s):
		"""
		Publishes the coordinate of the center of the cube to unity

		Args:
			x (float): x position of cube
			y (_type_): y position of cube
			z (_type_): z position of cube
			a (_type_): transparency of cube
			r (_type_): red colour of cube
			g (_type_): green colour of cube
			b (_type_): blue colour of cube
			s (_type_): size of cube
		"""
		js = JointState()
		js.header.stamp = rospy.Time.now()

		js.position = [x, y, z]
		js.velocity = [r, g, b, a]
		js.effort = [self.cube_res]

		self.unity_pub.publish(js)


	def snap_grid(self, x, y, z):
		"""
		Snaps a point to the closest point on the grid defined in the init function of the class

		Args:
			x (float): x position of the point
			y (float): y position of the point
			z (float): z position of the point

		Returns:
			_type_: a point representing the closest point on the grid to the position specified
		"""
		if self.cube_res_factor > 1:
			return np.around(x*(10/self.cube_res_factor), self.cube_res_places-1)/(10/self.cube_res_factor), np.around(y*(10/self.cube_res_factor), self.cube_res_places-1)/(10/self.cube_res_factor), np.around(z*(10/self.cube_res_factor), self.cube_res_places-1)/(10/self.cube_res_factor)
		return np.around(x*(10/self.cube_res_factor), self.cube_res_places)/(10/self.cube_res_factor), np.around(y*(10/self.cube_res_factor), self.cube_res_places)/(10/self.cube_res_factor), np.around(z*(10/self.cube_res_factor), self.cube_res_places)/(10/self.cube_res_factor)
		
def main(args):
	rospy.init_node('paint_publisher', anonymous=True, log_level=rospy.DEBUG)
	pp = paint_publisher()
	try:
		rospy.spin()
	except KeyboardInterrupt:
		print("Shutting down")

if __name__ == '__main__':
		main(sys.argv)