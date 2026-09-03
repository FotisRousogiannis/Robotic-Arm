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

## Control topology — distributed (ESP32 per segment)

Control is **distributed**: each topological segment of the arm carries
its own custom PCB with a local ESP32 controller. A central host (PC or
Raspberry Pi 4, running **Ubuntu Server** for native ROS 2) coordinates
all segments and runs the high-level stack; it does **not** drive servos
directly.

```
        ┌────────────────────────── Host (PC / Raspberry Pi 4) ──────────────────────────┐
        │   high-level control: targets out, joint state in, kinematics, planning        │
        └───────────────┬─────────────────────────────┬─────────────────────────────────┘
                        │ (micro-ROS)                 │ (micro-ROS)
             ┌──────────┴──────────┐        ┌─────────┴───────────┐
             │  Base PCB (ESP32)   │        │  Wrist PCB (ESP32)  │   ... one per segment
             │  joints 1, 2, 3     │        │  joints 4, 5, 6     │
             ├─────────────────────┤        ├─────────────────────┤
             │ PCA9685  → servos   │        │ PCA9685  → servos   │
             │ TCA9548A → AS5600   │        │ TCA9548A → AS5600   │
             │ buck converter      │        │ buck converter      │
             └─────────────────────┘        └─────────────────────┘
```

### Per-segment PCB
Each control PCB (e.g. the **base PCB** handling joints 1-2 differential +
joint 3) carries:

| Part          | Role                                                        |
|---------------|-------------------------------------------------------------|
| **ESP32**     | Local controller: closed-loop position control, host comms  |
| **PCA9685**   | 16-ch PWM servo driver (I²C)                                 |
| **TCA9548A**  | I²C multiplexer — lets several **AS5600** encoders share the bus (all fixed at 0x36) |
| **AS5600**    | Magnetic encoder on each axis → true joint position feedback|
| **Buck conv.**| Steps supply down to logic / sensor voltages                |

> Contact sensors on the gripper exist but are out of scope for now.

### Closed-loop position control
Unlike open-loop PWM, each ESP32 reads the **AS5600** angle on every axis
and can servo to a target position, compensating for gearbox backlash and
servo droop. Encoders sit behind the **TCA9548A** because every AS5600
answers at the same I²C address (0x36) — the ESP32 selects one mux channel
at a time to read each encoder.

### Host link — micro-ROS

Each ESP32 runs **micro-ROS**, so every segment PCB is a first-class ROS 2
node. The host (Ubuntu Server) runs the **micro-ROS Agent**, which bridges
the ESP32 nodes onto the normal ROS 2 graph.

```
ESP32 (base)  ──micro-ROS──┐
ESP32 (wrist) ──micro-ROS──┼──► micro-ROS Agent (host) ──► ROS 2 graph ──► robotic_arm_driver / MoveIt
ESP32 (...)   ──micro-ROS──┘        (UDP over WiFi, or serial)
```

Suggested per-segment interface (namespaced by segment):

| Topic                        | Dir       | Type                      |
|------------------------------|-----------|---------------------------|
| `/<seg>/joint_commands`      | host→ESP32| `sensor_msgs/JointState`  |
| `/<seg>/joint_states`        | ESP32→host| `sensor_msgs/JointState`  (from AS5600) |

- **Transport**: UDP over WiFi keeps each PCB wireless (only power to the
  segment); serial is the fallback for bring-up/debug.
- The ESP32 keeps its **local closed loop** (AS5600 → servo); micro-ROS
  carries targets in and true positions out.
- Run the agent on the host, e.g.
  `ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888`.

> The `segment_controller` firmware currently speaks a simple **serial**
> protocol for bench testing. The micro-ROS transport is layered on top of
> the same local control (see the firmware README roadmap).

## Electrical

- **Two isolated power rails** (built):
  1. Servo power — high-current rail for the GXservo motors
  2. Logic power — host + electronics (each PCB bucks down locally)
- **Servos**: GXservo 40 kg·cm (MG). See `Robotic_Arm_Project/Hardware/`.

> Keep the two grounds **commonly referenced** but the rails separate, so
> servo current transients don't brown out the logic / ESP32s.

## Software stack

- **Firmware — `software/firmware/`** (ESP32, per segment): drive servos
  via PCA9685, read AS5600 encoders through the TCA9548A, run the local
  position loop, talk to the host. *(link/protocol: to be decided)*
- **Bench tools — `software/tools/`**: standalone Python (no ROS) to
  test servos & gearboxes directly on a PCA9685 for quick checks.
- **Host — `software/ros2_ws/`**: ROS 2 stack that coordinates segments
  (`robotic_arm_driver` currently models differential mixing).
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
