cmake_minimum_required(VERSION 3.4)
project(panda_ros)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(catkin REQUIRED COMPONENTS
  controller_interface
  dynamic_reconfigure
  eigen_conversions
  franka_hw
  geometry_msgs
  hardware_interface
  std_msgs
  nav_msgs
  tf
  tf_conversions
  message_generation
  pluginlib
  realtime_tools
  roscpp
  rospy
)

find_package(Eigen3 REQUIRED)
find_package(Franka 0.7.0 REQUIRED)

add_message_files(FILES
  PoseCommand.msg
  StiffnessConfig.msg
  ForceOutput.msg
  ImpedanceParams.msg
  JointTorqueComparison.msg
  UnityInput.msg
  Vector3.msg
  Velocity.msg
  TrainingStatus.msg
)

add_service_files(
  FILES
  TrainingTrajectory.srv
)
generate_messages(DEPENDENCIES std_msgs dynamic_reconfigure nav_msgs geometry_msgs)

generate_dynamic_reconfigure_options(
  cfg/compliance_param.cfg
  cfg/desired_mass_param.cfg
  cfg/dual_arm_compliance_param.cfg
)

catkin_package(
  INCLUDE_DIRS include
  LIBRARIES panda_ros
  CATKIN_DEPENDS
    controller_interface
    dynamic_reconfigure
    eigen_conversions
    franka_hw
    geometry_msgs
    std_msgs
    nav_msgs
    geometry_msgs
    hardware_interface
    tf
    tf_conversions
    message_runtime
    pluginlib
    realtime_tools
    roscpp
  DEPENDS Franka
)

add_library(panda_ros
  src/joint_impedance_controller.cpp
  src/force_controller_NR.cpp
  src/cartesian_impedance_controller_NR.cpp
  src/cartesian_impedance_controller.cpp
  src/cartesian_impedance_equilibrium_controller.cpp
  src/cartesian_pose_impedance_controller.cpp
  src/joint_position_controller.cpp
  src/joint_velocity_controller.cpp
  src/dual_arm_cartesian_impedance_controller.cpp
)

add_dependencies(panda_ros
  ${${PROJECT_NAME}_EXPORTED_TARGETS}
  ${catkin_EXPORTED_TARGETS}
  ${PROJECT_NAME}_generate_messages_cpp
  ${PROJECT_NAME}_gencpp
  ${PROJECT_NAME}_gencfg
)

target_link_libraries(panda_ros PUBLIC
  ${Franka_LIBRARIES}
  ${catkin_LIBRARIES}
)

target_include_directories(panda_ros SYSTEM PUBLIC
  ${Franka_INCLUDE_DIRS}
  ${EIGEN3_INCLUDE_DIRS}
  ${catkin_INCLUDE_DIRS}
)
target_include_directories(panda_ros PUBLIC
  include
  ${catkin_INCLUDE_DIRS}
)

## Installation
install(TARGETS panda_ros
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
install(DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
install(DIRECTORY config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
install(FILES panda_ros_plugin.xml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
catkin_install_python(
  PROGRAMS 
  scripts/interactive_marker.py 
  scripts/move_to_start.py 
  scripts/dual_arm_interactive_marker.py
  scripts/robot_login.py
  scripts/hand_tracking.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## Tools
include(${CMAKE_CURRENT_LIST_DIR}/../cmake/ClangTools.cmake OPTIONAL
  RESULT_VARIABLE CLANG_TOOLS
)
if(CLANG_TOOLS)
  file(GLOB_RECURSE SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)
  file(GLOB_RECURSE HEADERS
    ${CMAKE_CURRENT_SOURCE_DIR}/include/*.h
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.h
  )
  add_format_target(panda_ros FILES ${SOURCES} ${HEADERS})
  add_tidy_target(panda_ros
    FILES ${SOURCES}
    DEPENDS panda_ros
  )
endif()
