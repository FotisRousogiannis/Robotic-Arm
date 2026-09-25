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

## 5. Couplings & interfaces
- **Output shaft → bevel gear**: spline (see §9a) — carries actuator torque
  into the differential.
- **Gearbox housing → arm body**: ISO 9409-1 flange (see §9b).
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

## 9. Output interfaces — ISO

Two distinct interfaces per actuator:
```
servo → planetary(1:36) → OUTPUT SHAFT ──[spline]──► BEVEL gear → differential
                          gearbox housing ──[FLANGE ISO 9409-1]──► arm body (mount)
```

### 9a. Output shaft → bevel gear (torque path)
Drives the differential's bevel gear — **backlash & centering are critical**
here (differential mixing degrades with play), so **spline preferred over
key**.
The shaft has two sections: a plain **Ø25 k6 journal** for the 6005 bearing,
and a **splined section** where the bevel gear mounts (spline is NOT at the
bearing seat).

| Feature | Standard | Value |
|---------|----------|-------|
| Spline (metric, involute, 30° PA) | **DIN 5480** (or ISO 4156) | shaft `W 25×1×24×8f` · hub `N 25×1×24×9H` (z = dB/m − 1.1 = 24) |
| Bearing seat (rotating inner ring) | ISO 286 | **Ø25 k6** |
| General tolerances | ISO 2768-m | non-critical dims |
| End chamfers | — | 1×45° |

> Stay **metric**: DIN 5480 involute spline (module-based) matches the rest
> of the metric standardization. Source metric splined shafts on TraceParts
> (`DIN 5480 spline shaft`) / Misumi, or model in Fusion. Avoid inch
> (McMaster) splined shafts — they force an inch-bore bearing at this seat.

> Spline chosen over a parallel key because it is printed anyway (no
> machining cost) and gives less backlash — important for clean pitch/roll
> decoupling in the differential. A DIN 6885 key remains a simpler fallback.

### 9b. Flange → arm body (mounting)
Mounts/reacts the gearbox housing to the arm structure — **ISO 9409-1**.
**Default: ISO 9409-1-50-4-M6**
- PCD **50 mm**, **4 × M6** (ISO 4762)
- centering **spigot H7/h7** (alignment by fit, not screws)
- Torque check (worst case 73.5 N·m): 73.5/0.025 = 2940 N ÷ 4 = **735 N/bolt**
  → M6 ample ✅
- Heavier option: **ISO 9409-1-63-6-M6** (PCD 63, 6 × M6)

Use the same flange across base / wrist / links for interchangeability.

## 10. Standard parts — sourcing (CAD)
Pull ready, dimensioned models into Fusion; model only custom parts.

| Part | Standard | Source (Fusion) |
|------|----------|-----------------|
| Bearings (6002/6005/6208…) | ISO | McMaster (Insert → McMaster-Carr) / TraceParts / Misumi |
| Screws (M3–M6 socket head) | ISO 4762 | McMaster / Fusion fastener lib / TraceParts |
| Parallel key 8×7 | DIN 6885-1 | TraceParts / Misumi |
| Precision shaft Ø25 k6 | ISO 286 | McMaster / Misumi (configurable) |
| Heat-set inserts M3 | — | McMaster |
| **ISO 9409-1 flange** | ISO 9409-1 | **model in Fusion** (spec, not a purchased part) |
| Gears (planetary/bevel) | — | model in Fusion (per §4) |

## 11. I²C address map (electronics, for reference)
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
- [ ] Output torque path: parallel key vs direct-through-flange
- [ ] Flange size: ISO 9409-1-50-4-M6 (default) vs 63-6-M6
- [ ] Bevel gear module/teeth (needs differential envelope)
- [ ] Placement of remaining bearings (6208 / 6004 / 6902)
- [ ] Planet gear face width (for tooth-stress recheck)
