#!/usr/bin/env python3
"""ROS 2 servo driver node for the robotic arm.

Subscribes to joint angle commands and drives GXservo motors through a
PCA9685 16-channel PWM controller over I2C.

Topics
------
subscribes:  /joint_commands  (sensor_msgs/JointState)
    Positions are interpreted as target angles in **degrees**, matched
    to joints by ``name``. Joints omitted from a message keep their last
    commanded angle.

The node reads its wiring/limits from ``config/servo_config.yaml``.

On a machine without the PCA9685 hardware/libraries (e.g. a laptop used
for development) the node automatically falls back to a "simulation"
backend that logs the PWM it *would* send, so the whole pipeline can be
tested off the robot.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class ServoBackend:
    """Abstracts the PWM hardware so the node can run on- or off-robot."""

    def __init__(self, node: Node, i2c_bus: int, address: int, frequency: int):
        self._node = node
        self._sim = False
        try:
            # Imported lazily so the package works without the hardware libs.
            from board import SCL, SDA  # type: ignore
            import busio  # type: ignore
            from adafruit_pca9685 import PCA9685  # type: ignore

            i2c = busio.I2C(SCL, SDA)
            self._pca = PCA9685(i2c, address=address)
            self._pca.frequency = frequency
            node.get_logger().info(
                f'PCA9685 initialised @ 0x{address:02x}, {frequency} Hz')
        except Exception as exc:  # noqa: BLE001 - any failure -> simulate
            self._sim = True
            self._pca = None
            node.get_logger().warn(
                f'PCA9685 unavailable ({exc}); running in SIMULATION mode.')
        self._frequency = frequency

    def set_pulse_us(self, channel: int, pulse_us: float) -> None:
        """Drive ``channel`` to a pulse width in microseconds."""
        if self._sim or self._pca is None:
            self._node.get_logger().debug(
                f'[sim] ch{channel:>2} <- {pulse_us:.0f} us')
            return
        period_us = 1_000_000.0 / self._frequency
        duty = int(max(0.0, min(1.0, pulse_us / period_us)) * 0xFFFF)
        self._pca.channels[channel].duty_cycle = duty


class ServoDriverNode(Node):
    def __init__(self) -> None:
        super().__init__('servo_driver')

        # --- global params ---
        i2c_bus = self.declare_parameter('i2c_bus', 1).value
        address = self.declare_parameter('pca9685_address', 0x40).value
        frequency = self.declare_parameter('pwm_frequency', 50).value
        self._joint_names = self.declare_parameter(
            'joint_names', []).value or []

        self._backend = ServoBackend(self, i2c_bus, address, frequency)

        # --- per-joint config ---
        self._joints: dict[str, dict] = {}
        for name in self._joint_names:
            prefix = f'joints.{name}'
            channels = self.declare_parameter(f'{prefix}.channels', []).value
            invert = self.declare_parameter(
                f'{prefix}.invert', [False] * len(channels)).value
            cfg = {
                'channels': list(channels),
                'invert': list(invert),
                'min_angle': float(self.declare_parameter(
                    f'{prefix}.min_angle', 0.0).value),
                'max_angle': float(self.declare_parameter(
                    f'{prefix}.max_angle', 180.0).value),
                'home': float(self.declare_parameter(
                    f'{prefix}.home', 90.0).value),
                'pulse_min': float(self.declare_parameter(
                    f'{prefix}.pulse_min', 500.0).value),
                'pulse_max': float(self.declare_parameter(
                    f'{prefix}.pulse_max', 2500.0).value),
            }
            self._joints[name] = cfg

        if not self._joints:
            self.get_logger().error(
                'No joints configured. Did you pass servo_config.yaml?')

        # Move everything to its home position on startup.
        for name, cfg in self._joints.items():
            self._command_joint(name, cfg['home'])

        self._sub = self.create_subscription(
            JointState, 'joint_commands', self._on_command, 10)
        self.get_logger().info(
            f'servo_driver ready — joints: {list(self._joints)}')

    def _angle_to_pulse(self, cfg: dict, angle: float, invert: bool) -> float:
        span = cfg['max_angle'] - cfg['min_angle']
        clamped = max(cfg['min_angle'], min(cfg['max_angle'], angle))
        frac = 0.0 if span == 0 else (clamped - cfg['min_angle']) / span
        if invert:
            frac = 1.0 - frac
        return cfg['pulse_min'] + frac * (cfg['pulse_max'] - cfg['pulse_min'])

    def _command_joint(self, name: str, angle: float) -> None:
        cfg = self._joints[name]
        for channel, invert in zip(cfg['channels'], cfg['invert']):
            pulse = self._angle_to_pulse(cfg, angle, invert)
            self._backend.set_pulse_us(channel, pulse)

    def _on_command(self, msg: JointState) -> None:
        if not msg.name or not msg.position:
            self.get_logger().warn('Received empty JointState; ignoring.')
            return
        for name, angle in zip(msg.name, msg.position):
            if name not in self._joints:
                self.get_logger().warn(f'Unknown joint "{name}"; skipping.')
                continue
            self._command_joint(name, float(angle))
            self.get_logger().debug(f'{name} -> {angle:.1f} deg')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ServoDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
