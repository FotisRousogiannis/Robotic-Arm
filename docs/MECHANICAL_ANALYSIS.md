# Mechanical Analysis

Engineering analysis of the actuator/drivetrain against the design targets.
All figures are estimates for design guidance; validate on hardware.

## Inputs (from BOM / standards)
| Parameter | Value |
|-----------|-------|
| Servo | QY3240MG, ~40 kg·cm ≈ **3.9 N·m stall**, continuous rotation |
| Servo free speed | ~300°/s (≈50 rpm) |
| Gearbox | 2-stage planetary, **1:6 × 1:6 = 1:36** |
| Efficiency (2 stages) | ~0.8 assumed |
| Differential | pitch uses **2 actuators** (torques add) |
| Arm self-weight | 5 kg, CoM ≈ 0.5 m |
| Target reach | 1.0 m |
| **Target payload** | **5 kg @ 1 m** |

## 1. Output speed & torque (per actuator, 1:36)
- Speed: 300 / 36 = **8.3°/s** (90° in ~11 s)
- Torque stall: 3.9 × 36 × 0.8 = **~112 N·m**
- Torque continuous (≈stall/3): **~37 N·m**

Differential (pitch, ×2):
| | per actuator | differential (×2) |
|--|--------------|-------------------|
| Stall | 112 N·m | **214 N·m** |
| Continuous | 37 N·m | **75 N·m** |

## 2. Torque required for 5 kg @ 1 m (worst case, horizontal)
| Component | Moment |
|-----------|--------|
| Payload 5 kg × 1.0 m | 49 N·m |
| Arm 5 kg × 0.5 m | 24.5 N·m |
| **Total** | **73.5 N·m** |

## 3. Does 1:36 meet it?
| Mode | Available (diff) | vs 73.5 N·m |
|------|------------------|-------------|
| Stall (momentary) | 214 N·m | SF ≈ 2.9 ✅ |
| Intermittent (~50% duty, pick-place) | ~112 N·m | SF ≈ 1.5 ✅ |
| Continuous hold (stall/3) | 75 N·m | SF ≈ 1.0 🟠 marginal |

**Conclusion:** 1:36 is the **right reduction** for 5 kg pick-and-place.
Lower ratios can't even hold the arm's own weight continuously; higher
ratios (1:48) hold better but are too slow (~6°/s) and worsen gear stress.
Continuous indefinite holding of 5 kg is marginal → needs a holding
strategy (§6).

### Reduction trade-off (continuous payload @1 m)
| Ratio | Output speed | Continuous payload | Gear stress |
|-------|--------------|--------------------|-------------|
| 1:18 | 17°/s | ~1.3 kg | medium |
| 1:24 | 12.5°/s | ~2.6 kg | high |
| **1:36** | 8.3°/s | ~5 kg | 🔴 very high |

## 4. Gear tooth loading (the critical issue)
Output stage transmits the full torque. Tangential force at the
planet↔ring mesh (pitch r_ring = 46.2 mm, 3 planets sharing):

    F_t = T / (r_ring × n_planets)
        = 141 N·m / (0.0462 m × 3) ≈ 1020 N per planet (at stall)
    (continuous ≈ 340 N)

On **module 1 printed teeth** this is very high — PLA/PETG teeth risk
shearing near stall/shock. **This is the real limit, not the ratio.**

Lewis check (σ = F_t / (b·m·Y), Y≈0.36 for 32T):
- To keep stress reasonable, either raise **module**, widen **face (b)**,
  or use a stronger **material** — strength scales with **b·m·material**.

### Fixes (output stage)
1. **Material: Nylon / PA-CF (or POM)** instead of PLA/PETG — 3–5× strength
   and far better wear. Biggest single win.
2. **Increase face width** — strength rises linearly with b; keeps the
   16/32/80 geometry unchanged (gears just get thicker).
3. **Firmware torque/current limit** — never approach stall.
4. (Optional) larger module **only on the output stage** if 1+2 aren't enough.

## 5. Helical thrust
Helix angle **30°** is high (typical 15–20°). Axial thrust:

    F_axial = F_t × tan(30°) ≈ 1020 × 0.577 ≈ 590 N per planet (stall)

Deep-groove 6002 bearings take limited axial load (~25% of radial).
**Recommendation:** reduce helix to **15–20°** to cut thrust, or ensure
adequate axial support.

## 6. Holding 5 kg without cooking the servos
A continuous-rotation servo holding a load stalls against it → heat.
Options:
- **Mechanical brake** on the joint (best for sustained holds).
- **Self-locking element** (e.g. a worm stage) if a redesign is acceptable.
- **Limit duty cycle** — fine if the arm mostly moves, rarely holds long.
- Rely on the **1:36 back-drive resistance** (helps but not self-locking).

## 7. Secondary notes
- **Planet wall thickness:** planet 32T m1 → root Ø ≈ 34 mm vs 6002 OD 32 mm
  → ~1 mm wall under the teeth. Consider a smaller-OD planet bearing
  (e.g. 6802/688) or a larger planet for more material.
- **Backlash** accumulates over 2 stages + differential; the output AS5600
  (closed loop) compensates static error but not reversal backlash.

## Summary — required changes for 5 kg
| # | Change | Priority |
|---|--------|----------|
| 1 | Output gears in Nylon/PA-CF + wider face width | 🔴 must |
| 2 | Holding strategy (brake / duty limit) | 🔴 must for sustained hold |
| 3 | Reduce helix to 15–20° | 🟠 recommended |
| 4 | Firmware torque/current limit | 🟠 recommended |
| 5 | Reduce arm weight / mass near base | 🟢 improves margin & speed |
| — | **Keep 1:36 reduction** | ✅ optimal for 5 kg |
