# Segment Controller (ESP32 firmware)

One firmware for every per-segment PCB (base, wrist, ...). Each board runs
the local control loop for its joints:

- **PCA9685** → servo PWM
- **TCA9548A** → I²C mux selecting one **AS5600** encoder at a time
- **AS5600** → true joint-angle feedback (all share address `0x36`, so the
  mux is required)

It exposes a simple **serial protocol** (USB, 115200 baud) so you can test
the wrist and gearboxes right away, before any host/ROS integration.

## Build & flash (PlatformIO)
```bash
cd software/firmware/segment_controller
pio run                 # build
pio run -t upload       # flash the ESP32
pio device monitor      # open serial monitor @115200
```

Configure the board via `-DSEGMENT_NAME=...` in `platformio.ini` and the
wiring/limits in `include/config.h`.

## Serial commands
| Command             | Action                                            |
|---------------------|---------------------------------------------------|
| `?`                 | print segment info (axes, channels)               |
| `P <axis> <deg>`    | set target angle for one axis (open-loop servo)   |
| `H`                 | home all axes (servo center)                      |
| `E`                 | print all encoder angles (deg)                    |
| `M <a> <b> <p> <r>` | differential mix test: servos a,b from pitch/roll |
| `R <axis>`          | release one axis servo (stop PWM)                  |

### Example wrist bring-up
```
?                 # confirm wiring
E                 # read encoders — move a joint by hand, watch it change
P 0 90            # command axis 0
M 0 1 15 0        # differential: pure pitch on servos ch0/ch1
M 0 1 0 15        # differential: pure roll
E                 # compare commanded vs actual (encoder) angle
```

## Calibration workflow
1. Flash, open the monitor, send `?` and `E`.
2. Turn each joint by hand and confirm the right encoder responds and the
   direction is correct (set `encoder_invert` in `config.h` if not).
3. Note the encoder reading at the mechanical home → set `encoder_offset`.
4. Command small servo angles with `P`; find the real `pulse_min/max` and
   `servo_min/max_angle` for each axis.
5. Copy the confirmed numbers into `config.h` (and the ROS 2 configs).

## Roadmap
- [ ] Closed-loop position control on the ESP32 (PID: encoder → servo)
- [ ] Host link — decide protocol (micro-ROS / WiFi / serial bridge)
- [ ] Publish joint state + accept targets from the ROS 2 host
