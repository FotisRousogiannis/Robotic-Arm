# System Architecture — Distributed ROS 2 + UI

Target architecture for the robotic arm: a **distributed ROS 2 system**
where a workstation does the heavy compute, a Raspberry Pi rides onboard as
a node/bridge, and each arm segment is driven by an ESP32 running
micro-ROS. A web dashboard controls everything and hosts manual and
autonomous (VLM) modes.

## Compute layers

```
┌──────────────── Clients: browsers (laptop / phone / tablet) ─────────────┐
│  thin — just open the URL, no install; download the dashboard            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │ WebSocket (rosbridge) + MJPEG (camera)
┌────────────────── Workstation (MAIN COMPUTE) ────────────────────────────┐
│  ROS 2                                                                    │
│   • web dashboard server (rosbridge_server, web_video_server / app)       │
│   • mode_manager        — arbitrates who commands the arm                 │
│   • vlm_agent           — camera + goal -> high-level actions (autonomous)│
│   • motion / kinematics — FK/IK, planning                                 │
│   • simulation          — URDF in RViz / Gazebo / Foxglove                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │ ROS 2 DDS (same domain, WiFi/LAN)
┌────────────────── Raspberry Pi (ONBOARD NODE / BRIDGE) ───────────────────┐
│  ROS 2                                                                    │
│   • micro-ROS Agent     — bridges the ESP32 nodes onto the graph          │
│   • camera node         — publishes /camera/image                         │
│   • (future) onboard brain for standalone autonomy                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                     micro-ROS (XRCE-DDS over WiFi/UDP or serial)
        ┌────────────────────────┼────────────────────────┐
   ┌────┴─────┐            ┌──────┴─────┐            ┌──────┴─────┐
   │ESP32 base│            │ESP32 wrist │            │ ESP32 ...  │   per-segment nodes
   │ PCA9685  │            │ PCA9685    │            │            │
   │ TCA9548  │            │ TCA9548    │            │            │
   │ AS5600 x │            │ AS5600 x   │            │            │
   └──────────┘            └────────────┘            └────────────┘
     servos + encoders, local closed-loop control
```

## Who runs what

| Layer | Runs on | Responsibilities |
|-------|---------|------------------|
| **Clients** | any browser | render dashboard, capture input — no install, nothing device-specific |
| **Main compute** | workstation/PC | ROS 2 brain: UI server, VLM, planning, kinematics, simulation, mode manager |
| **Onboard bridge** | Raspberry Pi (Ubuntu Server) | micro-ROS Agent, camera; keeps a path to standalone autonomy later |
| **Segment controllers** | ESP32 (one per PCB) | drive servos (PCA9685), read AS5600 via TCA9548, local position loop |

Why keep the Pi: it gives an **onboard ROS 2 presence** — the arm can carry
the micro-ROS Agent and camera locally, and later host an onboard brain for
standalone operation. The VLM stays on the workstation (or cloud): it is
too heavy for a Pi. For true onboard autonomy the Pi would be swapped for a
stronger board (e.g. Jetson) without changing the ROS graph.

## Communication (all ROS 2 native)

| Link | Protocol |
|------|----------|
| node ↔ node (workstation ↔ Pi) | **DDS** (ROS 2 default, same domain over WiFi/LAN) |
| ESP32 ↔ Agent | **micro-ROS / XRCE-DDS** (WiFi/UDP, serial fallback) |
| browser ↔ ROS | **rosbridge** (WebSocket) + **web_video_server** (MJPEG) |

## Core topics (draft)

| Topic | Dir | Type |
|-------|-----|------|
| `/<seg>/joint_commands` | →ESP32 | `sensor_msgs/JointState` (targets) |
| `/<seg>/joint_states` | ESP32→ | `sensor_msgs/JointState` (AS5600 feedback) |
| `/camera/image` | Pi→ | `sensor_msgs/Image` |
| `/mode` | UI→ | current mode (manual / autonomous / estop) |
| `/vlm/goal` | UI→ | natural-language task for the VLM |

## Modes

A `mode_manager` node arbitrates **who is allowed to publish commands**, so
manual and autonomous never fight:

- **Manual** — dashboard teleop drives `/joint_commands`.
- **Autonomous** — `vlm_agent` takes the camera + a goal and drives
  `/joint_commands`; the UI shows what it's doing.
- **E-stop** — everything neutral/stopped; overrides all.

## Reuse from the bench work

Everything already built carries over:
- **Calibration** (`software/tools/arm_calibration.json`): servo neutral
  1600 µs, range 500–2500, base = differential ch 0/1 (B inverted). These
  values move straight into the ESP32 firmware.
- **Differential mixing** (pitch = servos together, roll = servos opposed)
  becomes the per-segment logic in the ESP32 / `servo_driver`.
- **Bench tools** stay useful for quick hardware checks off-ROS.

## Phased plan

1. **Web teleop (now)** — dashboard skeleton controlling the base
   open-loop, structured to grow. Direct link today; swaps to ROS later.
2. **ROS bring-up** — servo/segment nodes + rosbridge; dashboard sends
   `/joint_commands`.
3. **Camera panel** — `web_video_server` MJPEG in the dashboard.
4. **Sim panel** — URDF in RViz/Foxglove or an embedded three.js viewer.
5. **micro-ROS on ESP32** — real per-segment controllers on the graph.
6. **Mode manager + VLM** — autonomous mode with the vision-language agent.

> Decision (locked): workstation = main compute; Raspberry Pi kept as the
> onboard ROS 2 node/bridge; ESP32 per segment via micro-ROS.
