# Bill of Materials (BOM)

## System performance (estimated)
| Metric | Value | Notes |
|--------|-------|-------|
| Payload @1 m | **~3–4 kg** continuous | after subtracting arm self-weight; ~19 kg momentary/stall |
| Joint speed | **~8.3°/s** | servo 300°/s ÷ 36; 90° in ~11 s |
| Joint torque (pitch, differential) | **~64 N·m** continuous / ~214 N·m stall | 2× actuators add |
| Arm self-weight | **4–5 kg** | CoM ~0.5 m assumed |
| Actuator | servo 40 kg + 1:36 planetary | continuous-rotation servo + AS5600 |

> Speed/torque trade-off: 1:36 gives high torque but is slow. A 1:18
> variant would double speed with still-ample torque (~10 kg payload gross).


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

## Bearings (deep-groove ball, 2RS sealed)

| Bearing | bore × OD × W (mm) | Notes | Likely joint | Status |
|---------|--------------------|-------|--------------|--------|
| 6902 2RS | 15 × 28 × 7 | thin-section, compact | wrist (light) | ✅ |
| 6002 2RS | 15 × 32 × 9 | standard 15 mm | wrist / small | ✅ |
| 6004 2RS | 20 × 42 × 12 | mid | bone2 | ✅ |
| 6005 2RS | 25 × 47 × 12 | mid-large | bone1 | ✅ |
| 6208 2RS | 40 × 80 × 18 | heavy, large | **base** (main rotation) | ✅ |

> "Likely joint" is a proposal — confirm which bearing sits where.

## Shafts / hubs (Ø = bearing bore, h7 fit)

Large bores → the bearing is usually the **joint pivot**: outer race held by
one part, a hub on the inner race rotates. So the "shaft" is often a hub /
short stub, not a long steel rod (and the bore can pass cables through).

| Joint | Ø (=bore) | Solid shaft or hub? | Status |
|-------|-----------|---------------------|--------|
| base | 40 | hub-in-bore (hollow → cabling) | ❓ |
| bone1 | 25 | ❓ | ❓ |
| bone2 | 20 | ❓ | ❓ |
| wrist | 15 | ❓ | ❓ |

## Drivetrain — planetary gearbox (per joint)

**2-stage planetary, 1:6 × 1:6 = 1:36 total.** Output shaft Ø25 on a
**6005** bearing. **AS5600 on the output** → true joint angle after
reduction.

Performance (servo QY3240MG 40 kg + 1:36, ~0.8 efficiency):
| | Servo | Output (÷36) |
|--|-------|--------------|
| Speed (no-load) | ~300°/s | **~8.3°/s** (90° in ~11 s) |
| Torque (stall) | 38 kg·cm | **~1090 kg·cm ≈ 107 N·m** (≈35 N·m continuous) |

> Trade-off: huge torque, slow. If more speed is wanted, a 1:18 variant
> (1:6 × 1:3) doubles output speed with still-ample torque.

Planetary standard (per 1:6 stage — ratio = 1 + Zring/Zsun, so Zring/Zsun = 5):
| Element | Teeth |
|---------|-------|
| Sun | 12 |
| Planet | 24 (×3 or ×4) |
| Ring | 60 |
- module: common per stage, 20° PA (proposed 1.0; 1.5 on output for torque)
- assembly check: (Zsun+Zring)=72 divisible by 3 and 4 ✓

## Gears — differentials
_Standard: 20° pressure angle; miter 1:1 @90°; module per envelope._

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

## Electronics

| Part | Role | Interface | Qty | Status |
|------|------|-----------|-----|--------|
| Raspberry Pi 4 (4 GB) | onboard ROS 2 node/bridge | — | 1 | ✅ |
| ESP32 | per-segment controller (planned PCBs) | — | per segment | ❓ |
| PCA9685 (16-ch, 12-bit PWM) | servo driver | I²C (0x40) | 1 | ✅ |
| TCA9548A (1→8 I²C mux) | fan out same-address AS5600 | I²C (0x70) | 1 | ✅ |
| AS5600 (12-bit magnetic encoder) | joint angle feedback | I²C (0x36, via mux) | 6 | ✅ |
| ADS1115 (16-bit ADC) | reads analog force sensors | I²C (0x48) | 5 | ✅ |
| FSR402 (force-sensitive resistor) | gripper contact/force | analog → ADS1115 | 2 | ✅ |
| KUAIQU SPS-C3010 PSU | main supply, 30 V/10 A, shows A | mains | 1 | ✅ |
| XY5008E DC-DC buck (6–55V, 5A, CC/CV) | step down to servo/logic rail | — | 2 | ✅ |

Notes:
- **AS5600 ×6** = one per DOF; all share I²C address 0x36 → the **TCA9548A**
  selects one at a time (why the mux is needed).
- **ADS1115 + FSR402** = gripper force/contact sensing (analog FSR → 16-bit
  ADC over I²C). Out of scope for current motion work.
- All I²C devices share the same bus (Pi now / ESP32 later): PCA9685 0x40,
  TCA9548A 0x70, ADS1115 0x48, AS5600 0x36 (behind mux).
