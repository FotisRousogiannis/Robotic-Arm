"""Bring up the servo driver with the wrist-only test profile."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('robotic_arm_driver'),
        'config', 'wrist_test.yaml')

    return LaunchDescription([
        Node(
            package='robotic_arm_driver',
            executable='servo_driver',
            name='servo_driver',
            output='screen',
            parameters=[config],
        ),
    ])
