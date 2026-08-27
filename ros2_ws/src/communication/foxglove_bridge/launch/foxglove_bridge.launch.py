import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("foxglove_bridge")
    # foxglove_bridge.yaml -> foxglove_bridge_params.yaml 로 일치
    default_config = os.path.join(pkg_dir, "config", "foxglove_bridge_params.yaml")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "params_file",
                default_value=default_config,
                description="Full path to the ROS 2 parameters YAML file",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="8765",
                description="WebSocket listening port for Foxglove Studio",
            ),
            DeclareLaunchArgument(
                "address",
                default_value="0.0.0.0",
                description="WebSocket listening address",
            ),
            Node(
                package="foxglove_bridge",
                executable="foxglove_bridge_node_exec",
                name="foxglove_bridge_node",
                output="screen",
                parameters=[
                    LaunchConfiguration("params_file"),
                    {
                        "port": LaunchConfiguration("port"),
                        "address": LaunchConfiguration("address"),
                    },
                ],
                remappings=[("/safety/failsafe_command", "/safety/failsafe_command")],
            ),
        ]
    )
