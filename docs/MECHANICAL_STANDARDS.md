# Mechanical Standards

Standardization rules so every part interfaces cleanly and future parts
"just fit". Apply these across all segments. Items marked ❓ need
confirmation against existing parts.

---

## 1. Fasteners
- **Socket head cap screws, ISO 4762 (DIN 912)**, metric, throughout.
- **M3** = primary · **M4 / M5** = structural / high-load.
- 3D-printed parts: **brass heat-set inserts (M3)** — never a screw straight
  into plastic.

## 2. Bearings (deep-groove ball, 2RS sealed)
Standardize on the set already in use:

| Bearing | bore × OD × W (mm) | Use |
|---------|--------------------|-----|
| 6902 2RS | 15 × 28 × 7 | wrist (thin/compact) |
| 6002 2RS | 15 × 32 × 9 | small joints |
| 6004 2RS | 20 × 42 × 12 | bone2 |
| 6005 2RS | 25 × 47 × 12 | bone1 / gearbox output |
| 6208 2RS | 40 × 80 × 18 | base (main rotation) |

## 3. Shafts / hubs
- **Shaft Ø = bearing bore**, tolerance **h7** (slip/press per fit needed).
- Large bores (≥20) → **hub-in-bore** (bearing = joint pivot; hub rotates on
  inner race), leaving the bore **hollow for cable routing**.
- A **flat / D-cut** where a set-screw lands, to prevent slip.

| Joint | Ø (=bore) | Bearing |
|-------|-----------|---------|
| base | 40 | 6208 |
| bone1 | 25 | 6005 |
| bone2 | 20 | 6004 |
| wrist | 15 | 6002 / 6902 |

## 4. Gears — global rules
- **Pressure angle: 20°** everywhere (non-negotiable for meshing).
- **Module: keep to few values.** Gears of different module DO NOT mesh.
  - Proposed: **module 1.0** general, **1.5** for high-torque output stages.
  - ❓ Align with the module of existing prints (`Gears/4h_mod_gear*`).
- **Min 17 teeth** on any pinion (avoid undercut); existing 22T spur is fine.
- **Center distance**: `C = module × (z₁ + z₂) / 2`.
- Printed material: **PETG** ok, **Nylon (PA)** preferred for loaded gears.

### 4a. Planetary gearbox (per joint)
2-stage, **1:6 × 1:6 = 1:36**. Per 1:6 stage (ratio = 1 + Zring/Zsun → 5):

| Element | Teeth |
|---------|-------|
| Sun | 12 |
| Planet | 24 (×3 or ×4 ❓) |
| Ring | 60 |

Assembly check: (Zsun + Zring) = 72, divisible by 3 and 4 ✓.

### 4b. Bevel gears (differentials)
- **Miter 1:1** (equal teeth), **90°**, 20° PA.
- Module & teeth sized to the mechanism envelope (❓ pending base/wrist space).
- Bore = shaft/hub Ø of that joint.

## 5. Couplings & servo interface
- **Servo output spline: 25T ❓ confirm** → standard **25T spline hub / disc
  horn** as the servo interface everywhere.
- **servo → sun gear** of the planetary via a 25T spline hub.
- **shaft ↔ shaft**: **clamp-type coupling** (no backlash) sized to shaft Ø,
  preferred over set-screw for precision.

## 6. Differential flanges
- **Common bolt pattern**: proposed **6 × M3 on PCD 30 mm**, identical on base
  and wrist → interchangeable flanges.
- **Spigot centering** (a locating lip) for alignment — not screws alone.

## 7. Tolerances & fits
- Shaft/bearing: **h7** shaft into bearing bore.
- Gear backlash (printed): target **0.10–0.15 mm** (set as CAD offset).

## 8. File naming convention (gears & shafts)
Encode the spec in the filename so mating parts are obvious:
```
spur_m1.5_z22_b25_PA20.stl      spur, module 1.5, 22T, bore 25, PA 20°
bevel_m1.5_z20_90deg_b25.stl    bevel, module 1.5, 20T, 90°, bore 25
planet_m1.0_z24_sun12_ring60.stl
shaft_d25_L120_h7.stl           shaft Ø25, length 120, h7
```

## 9. I²C address map (electronics, for reference)
| Device | Address |
|--------|---------|
| PCA9685 (PWM) | 0x40 |
| ADS1115 (ADC) | 0x48 |
| TCA9548A (mux) | 0x70 |
| AS5600 (encoder) | 0x36 (behind mux) |

---

## Open items to confirm
- [ ] Servo spline tooth count (25T?)
- [ ] Module of existing printed gears
- [ ] Planet count per stage (3 or 4)
- [ ] Bevel gear module/teeth (needs differential envelope)
- [ ] Differential flange PCD (proposed 30 mm)
