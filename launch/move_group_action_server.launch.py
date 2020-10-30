"""Launch move_group action server without controllers and trajectory execution"""

import os
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration


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
    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default=False)
    config_rviz2 = LaunchConfiguration('config_rviz2', default=os.path.join(get_package_share_directory("panda_moveit2_config"),
                                                                            "launch", "rviz.rviz"))

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

    # Trajectory Execution
    trajectory_execution = {"allow_trajectory_execution": False,
                            "moveit_manage_controllers": False}

    # Planning Scene
    planning_scene_monitor_parameters = {"publish_planning_scene": True,
                                         "publish_geometry_updates": True,
                                         "publish_state_updates": True,
                                         "publish_transforms_updates": True}

    return LaunchDescription([
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='If true, use simulated clock'),
        DeclareLaunchArgument(
            'config_rviz2',
            default_value=config_rviz2,
            description='Path to config for RViz2'),

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
                         planning_scene_monitor_parameters,
                         {'use_sim_time': use_sim_time}]),

        # RViz2
        Node(package="rviz2",
             executable="rviz2",
             name="rviz2",
             output="log",
             arguments=['--display-config', config_rviz2],
             parameters=[robot_description,
                         robot_description_semantic,
                         kinematics,
                         planning,
                         {'use_sim_time': use_sim_time}])
    ])
