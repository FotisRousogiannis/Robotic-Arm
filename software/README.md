# Software

The arm's software is organized in two tracks so you can move fast now
and still build the proper stack for the thesis.

```
software/
├── firmware/       # ESP32 firmware — the on-board control per segment PCB.
│   └── segment_controller/   PCA9685 + TCA9548A + AS5600, serial protocol.
├── tools/          # Standalone scripts — NO ROS needed. Quick bench test
│   └── servo_test.py   of a servo/gearbox straight off a PCA9685.
└── ros2_ws/        # ROS 2 workspace — the host-side coordination stack.
    └── src/robotic_arm_driver/
```

The real control is **distributed**: each segment PCB runs
`firmware/segment_controller` on its ESP32 (servo drive + encoder
feedback), and the ROS 2 host coordinates all segments. See
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for the topology.
`tools/servo_test.py` is only for quick bench checks before the boards
are wired in.

## Track 1 — Quick hardware tests (no ROS)

Goal right now: **verify the wrist and its gearboxes** before building
Link 1. `tools/servo_test.py` drives the PCA9685 directly.

### On the Raspberry Pi — Ubuntu Server (once)
Ubuntu Server has no `raspi-config`; enable I²C via the firmware config:
```bash
sudo nano /boot/firmware/config.txt      # add:  dtparam=i2c_arm=on
sudo apt install -y i2c-tools python3-pip
sudo usermod -aG i2c $USER               # then log out/in
sudo reboot
# after reboot:
pip install adafruit-circuitpython-pca9685 adafruit-blinka
i2cdetect -y 1                           # should show PCA9685 at 0x40
```

> Note: in the final design the ESP32 on each PCB drives the PCA9685, not
> the Pi. This direct-from-Pi path is only for quick bench testing of a
> servo/gearbox before the boards are in the loop.

### Test sequence (start gentle!)
```bash
cd software/tools

# 1. Center the wrist servos (find your real centers first):
python3 servo_test.py center --channels 8 9 10 11 --min 0 --max 270

# 2. Move ONE servo a little and confirm direction:
python3 servo_test.py set --channel 9 --angle 135 --min 0 --max 270

# 3. Slow, small sweep to watch a gearbox for binding/backlash:
python3 servo_test.py sweep --channel 9 --min 0 --max 270 \
        --start 120 --end 150 --step 2 --dwell 0.1

# 4. Differential check (wrist pitch/roll from 2 servos):
python3 servo_test.py diff --a 9 --b 10 --pitch 15 --roll 0   # pure pitch
python3 servo_test.py diff --a 9 --b 10 --pitch 0  --roll 15  # pure roll

# 5. Release when done:
python3 servo_test.py release --channels 8 9 10 11
```

> Runs in **SIMULATION mode** (prints pulses) on any machine without the
> PCA9685 libs, so you can dry-run commands on your laptop first.

**Safety:** keep a hand on the power switch; stop immediately if a servo
stalls, buzzes, or a gearbox binds. Increase travel only once direction
and limits are confirmed.

Record the real centers / min / max you find — they become the
calibration values in the ROS 2 config below.

## Track 2 — ROS 2 stack

`ros2_ws/src/robotic_arm_driver` — a ROS 2 (rclpy) node that subscribes
to `/joint_commands` (`sensor_msgs/JointState`, degrees) and drives the
servos, with **differential mixing** for the base and wrist.

### Build & run (on the Pi, ROS 2 installed)
```bash
cd software/ros2_ws
colcon build --packages-select robotic_arm_driver
source install/setup.bash

# Wrist-only bring-up:
ros2 launch robotic_arm_driver wrist_test.launch.py

# Command the wrist pitch to 15 deg from another terminal:
ros2 topic pub --once /joint_commands sensor_msgs/msg/JointState \
  '{name: ["wrist_pitch"], position: [15.0]}'
```

Calibration lives in `config/wrist_test.yaml` (wrist only) and
`config/servo_config.yaml` (full arm). Update the channel numbers,
centers, gains and pulse limits from what you measured in Track 1.

See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) for the DOF map,
differential mixing math, and roadmap.
