# Bill of Materials (BOM)

Master components list for the robotic arm — single source of truth.
Add items as they are chosen/ordered. Quantities are per full arm unless
noted. Keep in sync with `Robotic_Arm_Project/Hardware/`.

Legend: ✅ have it · 🛒 to order · ❓ to decide

---

## Actuators

### Servo — QY3240MG pro (40 kg, continuous rotation)
| Field | Value |
|-------|-------|
| Model | QY3240MG pro |
| Type | **Continuous rotation**, digital, metal gear (copper & aluminum) |
| Torque (stall) | 35 kg·cm @6V · 38 kg·cm @7.4V |
| Speed (no load) | 0.2 s/60° @6V · 0.19 s/60° @7.4V (≈ 300°/s ≈ 50 rpm) |
| Operating voltage | **5.0–7.4 V** |
| Signal | neutral **~1520 µs**, up to 333 Hz (we drive at 50 Hz) |
| Dead band | 3 µs |
| Size / weight | 40.5 × 40 × 20.2 mm · 73 g |
| Spline | ❓ confirm (typically 25T for this class) |
| Status | ✅ in use |

Notes:
- Measured neutral on the bench: **~1600 µs** (per-servo trim; spec says 1520).
- Bench range used: 500–2500 µs. All servos on the arm are this model.

Quantities (from the electrical components list):
- base: 1 · bone1: 4 · bone2: 4 · end effector: 3 → see
  `Robotic_Arm_Project/Hardware/Electrical Components.md`

---

## Bearings
_TBD — user to provide codes/dimensions (bore × OD × width)._

| Location | Bearing | bore×OD×W | Qty | Status |
|----------|---------|-----------|-----|--------|
| | | | | 🛒 |

## Shafts
_Derived from bearing bore (Ø = bore, h7 fit). TBD once bearings known._

| Location | Ø × length | Material | Qty | Status |
|----------|-----------|----------|-----|--------|
| | | | | ❓ |

## Gears (differentials & reductions)
_Standard: 20° pressure angle; module TBD from existing prints._

| Use | Type | module / teeth | bore | Qty | Status |
|-----|------|----------------|------|-----|--------|
| base differential | bevel/miter @90° | | | | ❓ |
| wrist differential | bevel/miter @90° | | | | ❓ |

## Couplings
_bore = shaft Ø; interface = servo spline. TBD._

| From → To | Type | bore | Qty | Status |
|-----------|------|------|-----|--------|
| servo → shaft | | | | ❓ |

---

## Electronics (summary — see Hardware/Electrical Components.md)
- Raspberry Pi 4 (4 GB) — onboard ROS 2 node/bridge
- PCA9685 16-ch PWM driver (I²C)
- TCA9548A I²C multiplexer (for AS5600 encoders)
- AS5600 magnetic encoders (per axis)
- KUAIQU SPS-C3010 PSU (30V/10A) + XY5008E buck converters
- ESP32 (per-segment controllers — planned PCBs)
