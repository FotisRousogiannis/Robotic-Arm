#!/usr/bin/env python3
"""ROS 2 servo driver node for the robotic arm.

Subscribes to logical joint angle commands and drives GXservo motors
through a PCA9685 16-channel PWM controller over I2C. Supports two kinds
of joints:

* **direct** joints  — one logical DOF -> one servo channel (yaw, gripper)
* **differential** pairs — two servos combine to produce two DOF
  (pitch + roll), as on this arm's base and wrist. Motor angles are:

      A = center_a + pitch_gain*pitch + roll_gain*roll
      B = center_b + pitch_gain*pitch - roll_gain*roll

Topics
------
subscribes:  /joint_commands  (sensor_msgs/JointState)
    positions = target angles in **degrees**, matched to joints by name.
    Joints omitted from a message keep their last commanded value.

On a machine without the PCA9685 libraries the node falls back to a
"simulation" backend that logs the PWM it would send, so the pipeline
can be tested off the robot.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class ServoBackend:
    """Abstracts the PWM hardware so the node runs on- or off-robot."""

    def __init__(self, node: Node, address: int, frequency: int):
        self._node = node
        self._frequency = frequency
        self._sim = False
        self._pca = None
        try:
            from board import SCL, SDA  # type: ignore
            import busio  # type: ignore
            from adafruit_pca9685 import PCA9685  # type: ignore

            i2c = busio.I2C(SCL, SDA)
            self._pca = PCA9685(i2c, address=address)
            self._pca.frequency = frequency
            node.get_logger().info(
                f'PCA9685 initialised @ 0x{address:02x}, {frequency} Hz')
        except Exception as exc:  # noqa: BLE001
            self._sim = True
            node.get_logger().warn(
                f'PCA9685 unavailable ({exc}); running in SIMULATION mode.')

    def set_pulse_us(self, channel: int, pulse_us: float) -> None:
        if self._sim or self._pca is None:
            self._node.get_logger().info(
                f'[sim] ch{channel:>2} <- {pulse_us:.0f} us')
            return
        period_us = 1_000_000.0 / self._frequency
        duty = int(max(0.0, min(1.0, pulse_us / period_us)) * 0xFFFF)
        self._pca.channels[channel].duty_cycle = duty


def _angle_to_pulse(angle, a_min, a_max, p_min, p_max, invert=False):
    """Map an angle in [a_min, a_max] to a pulse width in [p_min, p_max]."""
    span = a_max - a_min
    clamped = max(a_min, min(a_max, angle))
    frac = 0.0 if span == 0 else (clamped - a_min) / span
    if invert:
        frac = 1.0 - frac
    return p_min + frac * (p_max - p_min)


class ServoDriverNode(Node):
    def __init__(self) -> None:
        super().__init__('servo_driver')

        address = self.declare_parameter('pca9685_address', 0x40).value
        frequency = self.declare_parameter('pwm_frequency', 50).value
        self.declare_parameter('i2c_bus', 1)  # informational

        self._backend = ServoBackend(self, address, frequency)

        # Current target angle for every logical DOF.
        self._targets: dict[str, float] = {}

        self._direct: dict[str, dict] = {}
        self._diffs: list[dict] = []

        self._load_direct_joints()
        self._load_differentials()

        if not self._direct and not self._diffs:
            self.get_logger().error(
                'No joints configured. Did you pass a config YAML?')

        # Drive everything to its home/center pose on startup.
        self._apply_all()

        self._sub = self.create_subscription(
            JointState, 'joint_commands', self._on_command, 10)
        self.get_logger().info(
            f'servo_driver ready — DOF: {sorted(self._targets)}')

    # ------------------------------------------------------------------ config
    def _load_direct_joints(self) -> None:
        names = self.declare_parameter('direct_joints', []).value or []
        for name in names:
            p = f'joints.{name}'
            cfg = {
                'channel': int(self.declare_parameter(f'{p}.channel', 0).value),
                'invert': bool(self.declare_parameter(f'{p}.invert', False).value),
                'min_angle': float(self.declare_parameter(f'{p}.min_angle', 0.0).value),
                'max_angle': float(self.declare_parameter(f'{p}.max_angle', 180.0).value),
                'home': float(self.declare_parameter(f'{p}.home', 90.0).value),
                'pulse_min': float(self.declare_parameter(f'{p}.pulse_min', 500.0).value),
                'pulse_max': float(self.declare_parameter(f'{p}.pulse_max', 2500.0).value),
            }
            self._direct[name] = cfg
            self._targets[name] = cfg['home']

    def _load_differentials(self) -> None:
        pairs = self.declare_parameter('differential_pairs', []).value or []
        for name in pairs:
            p = f'differentials.{name}'
            pitch = self.declare_parameter(f'{p}.joint_pitch', f'{name}_pitch').value
            roll = self.declare_parameter(f'{p}.joint_roll', f'{name}_roll').value
            cfg = {
                'name': name,
                'channel_a': int(self.declare_parameter(f'{p}.channel_a', 0).value),
                'channel_b': int(self.declare_parameter(f'{p}.channel_b', 1).value),
                'joint_pitch': pitch,
                'joint_roll': roll,
                'center_a': float(self.declare_parameter(f'{p}.center_a', 90.0).value),
                'center_b': float(self.declare_parameter(f'{p}.center_b', 90.0).value),
                'pitch_gain': float(self.declare_parameter(f'{p}.pitch_gain', 1.0).value),
                'roll_gain': float(self.declare_parameter(f'{p}.roll_gain', 1.0).value),
                'servo_min_angle': float(self.declare_parameter(f'{p}.servo_min_angle', 0.0).value),
                'servo_max_angle': float(self.declare_parameter(f'{p}.servo_max_angle', 180.0).value),
                'pulse_min': float(self.declare_parameter(f'{p}.pulse_min', 500.0).value),
                'pulse_max': float(self.declare_parameter(f'{p}.pulse_max', 2500.0).value),
            }
            self._diffs.append(cfg)
            self._targets.setdefault(pitch, 0.0)
            self._targets.setdefault(roll, 0.0)

    # ------------------------------------------------------------------ drive
    def _apply_direct(self, name: str) -> None:
        cfg = self._direct[name]
        pulse = _angle_to_pulse(
            self._targets[name], cfg['min_angle'], cfg['max_angle'],
            cfg['pulse_min'], cfg['pulse_max'], cfg['invert'])
        self._backend.set_pulse_us(cfg['channel'], pulse)

    def _apply_diff(self, cfg: dict) -> None:
        pitch = self._targets[cfg['joint_pitch']]
        roll = self._targets[cfg['joint_roll']]
        angle_a = cfg['center_a'] + cfg['pitch_gain'] * pitch + cfg['roll_gain'] * roll
        angle_b = cfg['center_b'] + cfg['pitch_gain'] * pitch - cfg['roll_gain'] * roll
        for channel, angle in ((cfg['channel_a'], angle_a), (cfg['channel_b'], angle_b)):
            pulse = _angle_to_pulse(
                angle, cfg['servo_min_angle'], cfg['servo_max_angle'],
                cfg['pulse_min'], cfg['pulse_max'])
            self._backend.set_pulse_us(channel, pulse)

    def _apply_all(self) -> None:
        for name in self._direct:
            self._apply_direct(name)
        for cfg in self._diffs:
            self._apply_diff(cfg)

    # ------------------------------------------------------------------ topic
    def _on_command(self, msg: JointState) -> None:
        if not msg.name or not msg.position:
            self.get_logger().warn('Received empty JointState; ignoring.')
            return

        touched_direct: set[str] = set()
        touched_diff: set[str] = set()
        for name, angle in zip(msg.name, msg.position):
            if name not in self._targets:
                self.get_logger().warn(f'Unknown DOF "{name}"; skipping.')
                continue
            self._targets[name] = float(angle)
            if name in self._direct:
                touched_direct.add(name)
            for cfg in self._diffs:
                if name in (cfg['joint_pitch'], cfg['joint_roll']):
                    touched_diff.add(cfg['name'])

        for name in touched_direct:
            self._apply_direct(name)
        for cfg in self._diffs:
            if cfg['name'] in touched_diff:
                self._apply_diff(cfg)


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
