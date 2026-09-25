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

| Bearing | bore × OD × W (mm) | Use (actual) |
|---------|--------------------|--------------|
| 6002 2RS | 15 × 32 × 9 | **planet gears** (each planet rotates on a 6002) |
| 6005 2RS | 25 × 47 × 12 | **shafts / joint output axes** (Ø25) |
| 6902 2RS | 15 × 28 × 7 | ❓ (thin-section, TBD) |
| 6004 2RS | 20 × 42 × 12 | ❓ TBD |
| 6208 2RS | 40 × 80 × 18 | ❓ likely base main rotation, TBD |

## 3. Shafts / hubs
- **Shaft Ø = bearing bore**, tolerance **h7** (slip/press per fit needed).
- Large bores (≥20) → **hub-in-bore** (bearing = joint pivot; hub rotates on
  inner race), leaving the bore **hollow for cable routing**.
- A **flat / D-cut** where a set-screw lands, to prevent slip.

| Element | Ø (=bore) | Bearing |
|---------|-----------|---------|
| output / joint shaft | 25 | 6005 |
| planet gear | 15 | 6002 |
| base main rotation | 40 | 6208 (TBD) |

## 4. Gears — global rules
- **Pressure angle: 20°** everywhere (non-negotiable for meshing).
- **Module: keep to few values.** Gears of different module DO NOT mesh.
  - Planetary gears: **helical, normal module mₙ = 1, helix 30°** (actual).
  - **Min ~17 teeth** on a pinion for spur; helical tolerates fewer (sun is
    16T helical — OK thanks to the helix angle raising virtual tooth count).
- **Center distance**: `C = module × (z₁ + z₂) / 2`.
- Printed material: **PETG** ok, **Nylon (PA)** preferred for loaded gears.

### 4a. Planetary gearbox (per joint) — ACTUAL design
2-stage, **1:6 × 1:6 = 1:36**. **Helical gears, 30° helix angle.**

| Element | Teeth | Hand | File |
|---------|-------|------|------|
| Sun | 16 | L | Sun Helical Gear (16L@30.00) |
| Planet (×3) | 32 | R | Healical Gear (32R@30.00) |
| Ring | 80 | R | Ring Gear |

- **Normal module mₙ = 1**, **helix angle β = 30°**, 20° PA.
- Ratio = 1 + 80/16 = **6.0** ✅ · 3 planets: (16+80)/3 = 32 ✓
- Helix hand: sun L, planet R (external mesh = opposite), ring R (internal =
  same as planet) ✓
- Transverse module mₜ = mₙ/cos β = 1/cos30° = **1.1547**.
  Pitch diameters (d = mₜ·z): sun 18.48 · planet 36.95 · ring 92.38 mm.
  Center distance sun↔planet = (18.48+36.95)/2 = **27.7 mm**
  = (ring−planet)/2 ✓ consistent.
- Helical gears create **axial thrust** — deep-groove bearings absorb it;
  keep it in mind for shaft location.
- Housing parts (CAD): Ring Gear, Planet Carrier, Planet Carrier Rotating
  Base, Cap, Servo holder, Servo Cap, servo arm cap.

### 4b. Bevel gears (differentials)
- **Miter 1:1** (equal teeth), **90°**, 20° PA.
- Module & teeth sized to the mechanism envelope (❓ pending base/wrist space).
- Bore = shaft/hub Ø of that joint.

## 5. Couplings & servo interface
- **Servo output spline: 25T** (standard for 35–40 kg standard-size servos;
  spline Ø ≈ 5.9 mm — confirm by counting teeth / checking the horns) →
  standard **25T spline hub / disc horn** as the servo interface everywhere.
- **servo → sun gear**: uses the **stock metal servo horn** (25T, included
  with the servo). The sun gear (or a printed adapter) bolts onto the horn
  through its screw holes — no separate hub needed. Standardize the sun/
  adapter to match the horn's bolt pattern.
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

## Confirmed
- [x] Planetary: helical, mₙ=1, 30° helix, sun 16 / planet 32 (×3) / ring 80
- [x] Planet count: 3

## Confirmed (cont.)
- [x] Servo interface: stock metal 25T horn drives the sun gear
- [x] Servo spline: 25T

## Open items to confirm
- [ ] Bevel gear module/teeth (needs differential envelope)
- [ ] Differential flange PCD (proposed 30 mm)
- [ ] Placement of remaining bearings (6208 / 6004 / 6902)
