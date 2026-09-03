# Robotic Arm — Architecture

Single source of truth for the arm's mechanical, electrical and software
structure. Keep this file updated as the design evolves.

## Degrees of freedom

The arm targets **6 DOF** plus a gripper. It uses two **differential
mechanisms** (base and wrist): in each, two servos move together to
produce two rotational DOF.

| Segment      | DOF | Mechanism             | Status              |
|--------------|-----|-----------------------|---------------------|
| Base         | 2   | Differential (pitch + roll) | ✅ built       |
| Link 1       | 1   | (planned)             | ❌ not built yet    |
| Wrist        | 3   | Differential (pitch + roll) + yaw | ✅ built |
| Gripper      | 1   | Direct servo, camera mount  | ✅ built       |

> Link 1 is intentionally left for last so the wrist can be tested and
> calibrated independently first. The base and the far end of the wrist
> share a similar differential design.

## Logical joints (`/joint_commands`)

Commands are `sensor_msgs/JointState`, positions in **degrees**, matched
by name:

- `base_pitch`, `base_roll`   → base differential (channels 0, 1)
- `wrist_pitch`, `wrist_roll` → wrist differential (channels 9, 10)
- `wrist_yaw`                  → direct servo (channel 8)
- `gripper`                   → direct servo (channel 11)

### Differential mixing

For a differential pair, the two motor angles are:

```
motor_A = center_a + pitch_gain * pitch + roll_gain * roll
motor_B = center_b + pitch_gain * pitch - roll_gain * roll
```

- Pure **pitch**: both motors rotate the same direction.
- Pure **roll**: motors rotate opposite directions.

`center_*`, `*_gain`, and the servo travel/pulse limits are calibrated
per mechanism in the config YAML.

## Electrical

- **Two isolated power rails** (built):
  1. Servo power — high-current rail for the GXservo motors
  2. Logic power — Raspberry Pi 4 + electronics
- **Controller**: Raspberry Pi 4 (4 GB), I²C to a PCA9685 (16-ch, 12-bit PWM).
- **Servos**: GXservo 40 kg·cm (MG). See `Robotic_Arm_Project/Hardware/`.

> Keep the two grounds **commonly referenced** but the rails separate, so
> servo current transients don't brown out the Pi.

## Software stack

- **Track 1 — `software/tools/`**: standalone Python (no ROS) to test the
  wrist & gearboxes now.
- **Track 2 — `software/ros2_ws/`**: ROS 2 stack.
  - `robotic_arm_driver` — servo driver node with differential mixing.
- **CAD**: Fusion 360 model (incomplete — Link 1 pending). Will be the
  source for the URDF once the geometry is finalized.
- Planned: URDF/description, kinematics (FK/IK), MoveIt, teleop, vision
  (gripper camera).

## Roadmap

1. ✅ Mechanical: base, wrist, gripper
2. ✅ Electrical: components, dual power rails
3. ▶️ **Software: drive & calibrate the wrist** (current)
4. ⬜ Build & integrate Link 1 → full 6-DOF
5. ⬜ URDF + kinematics
6. ⬜ Teleop / vision-based tasks
