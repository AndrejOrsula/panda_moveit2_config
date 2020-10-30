"""Example of using fake_joint_driver to control panda in RViz2"""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def load_file(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return file.read()
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_file_path = os.path.join(package_path, file_path)

    try:
        with open(absolute_file_path, "r") as file:
            return yaml.safe_load(file)
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None


def generate_launch_description():
    # URDF
    robot_urdf_config = load_file("panda_ign",
                                  "urdf/panda.urdf")
    robot_description = {"robot_description": robot_urdf_config}

    # SRDF
    robot_srdf = load_file("panda_moveit2_config",
                           "srdf/panda.srdf")
    robot_description_semantic = {"robot_description_semantic": robot_srdf}

    # Kinematics
    kinematics = load_yaml("panda_moveit2_config",
                           "config/kinematics.yaml")

    # Planning
    ompl_yaml = load_yaml("panda_moveit2_config",
                          "config/ompl_planning.yaml")
    planning = {"move_group": {
        "planning_plugin": "ompl_interface/OMPLPlanner",
        "request_adapters": """default_planner_request_adapters/AddTimeOptimalParameterization default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints""",
        "start_state_max_bounds_error": 0.1}}
    planning["move_group"].update(ompl_yaml)

    # Controllers
    controllers_yaml = load_yaml("panda_moveit2_config",
                                 "config/fake_control/controllers.yaml")
    moveit_controllers = {"moveit_simple_controller_manager": controllers_yaml,
                          "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager"}

    # Trajectory Execution
    trajectory_execution = {"allow_trajectory_execution": True,
                            "moveit_manage_controllers": True,
                            "trajectory_execution.allowed_execution_duration_scaling": 1.2,
                            "trajectory_execution.allowed_goal_duration_margin": 0.5,
                            "trajectory_execution.allowed_start_tolerance": 0.01}

    # Planning Scene
    planning_scene_monitor_parameters = {"publish_planning_scene": True,
                                         "publish_geometry_updates": True,
                                         "publish_state_updates": True,
                                         "publish_transforms_updates": True}

    return LaunchDescription([
        # Start move_group action server
        Node(package="moveit_ros_move_group",
             executable="move_group",
             name="move_group",
             output="screen",
             parameters=[robot_description,
                         robot_description_semantic,
                         kinematics,
                         planning,
                         trajectory_execution,
                         moveit_controllers,
                         planning_scene_monitor_parameters]),

        # Static TF
        Node(package="tf2_ros",
             executable="static_transform_publisher",
             name="static_transform_publisher_world_robot",
             output="screen",
             arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "panda_link0"]),

        # Robot state publisher
        Node(package="robot_state_publisher",
             executable="robot_state_publisher",
             name="robot_state_publisher",
             output="screen",
             parameters=[robot_description]),

        # Fake joint driver
        Node(package="fake_joint_driver",
             executable="fake_joint_driver_node",
             parameters=[{"controller_name": "panda_arm_controller"},
                         robot_description,
                         os.path.join(get_package_share_directory(
                             "panda_moveit2_config"), "config", "fake_control", "panda_arm_controller.yaml"),
                         os.path.join(get_package_share_directory(
                             "panda_moveit2_config"), "config", "fake_control", "start_position.yaml")]),

        # RViz2
        Node(package="rviz2",
             executable="rviz2",
             name="rviz2",
             output="log",
             arguments=["-d",
                        os.path.join(get_package_share_directory("panda_moveit2_config"),
                                     "launch", "rviz_interactive.rviz")],
             parameters=[robot_description,
                         robot_description_semantic,
                         kinematics,
                         planning])
    ])
