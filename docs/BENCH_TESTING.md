# Bench Testing — Speed & Current (Pi + PCA9685)

Practical guide for the current setup: **Raspberry Pi (Ubuntu Server) →
PCA9685 → servo/gearbox**, no PCB/ESP32 yet. Goal: measure each gearbox's
**speed** and **current draw** ("how much it eats").

## 0. The setup right now

```
  PC/laptop ──SSH──► Raspberry Pi (Ubuntu Server) ──I²C──► PCA9685 ──PWM──► servo ─► gearbox
                          (runs the code)                    ▲
                                                             │ servo V+ from the
                     KUAIQU PSU (servo rail, shows V & A) ───┘ high-current rail
```

- You **write code on your PC** (in this repo), push to GitHub, and **pull
  it on the Pi**. You then **SSH into the Pi** and run the tool there —
  the Pi is what physically talks to the PCA9685 over I²C.
- The PCA9685's **V+ (servo power)** comes from the **KUAIQU PSU**, whose
  display shows the **current (A)** the servos draw — that is your current
  measurement, no extra sensor needed.
- PCA9685 **logic (VCC)**, **SDA**, **SCL**, **GND** go to the Pi. The
  servo-power ground and the Pi ground **must be joined** (common GND).

## 1. Get the repo onto the Pi (once)

SSH in from your PC:
```bash
ssh <user>@<pi-ip-address>
```
Then clone this repo on the Pi:
```bash
sudo apt update && sudo apt install -y git python3-pip i2c-tools
git clone https://github.com/FotisRousogiannis/Robotic-Arm.git
cd Robotic-Arm
```
Enable I²C (Ubuntu Server — no raspi-config):
```bash
sudo nano /boot/firmware/config.txt     # add line:  dtparam=i2c_arm=on
sudo usermod -aG i2c $USER
sudo reboot
```
After reboot, install the driver lib and confirm the chip is seen:
```bash
pip install adafruit-circuitpython-pca9685 adafruit-blinka
i2cdetect -y 1        # expect 0x40 (PCA9685)
```

### Updating the code later
Whenever we change the code here, on the Pi just:
```bash
cd ~/Robotic-Arm && git pull
```

## 2. How you send commands

You type commands in the **SSH terminal on the Pi**. They run
`software/tools/servo_test.py`, which sends PWM to the PCA9685. Example —
first make sure it responds (safe, no motion needed to check wiring):
```bash
cd ~/Robotic-Arm/software/tools
python3 servo_test.py set --channel 9 --angle 135 --min 0 --max 270
```
> On the Pi with the PCA9685 wired, this moves the servo. On your PC
> (no chip) the same command runs in SIMULATION and just prints the pulse.

## 3. Speed test

Move a joint end-to-end at a controlled rate; the tool reports the
effective deg/s:
```bash
# 90 -> 180 deg at 60 deg/s on channel 9:
python3 servo_test.py move --channel 9 --start 90 --end 180 \
        --speed 60 --min 0 --max 270
```
- Try increasing `--speed` until the servo can't keep up (the *effective*
  deg/s stops rising) — that's the gearbox's practical top speed.
- Time a full range both directions to check it's symmetric.

## 4. Current draw test ("πόσο τρώει")

Read **Amps on the KUAIQU PSU display** during three conditions:

| Condition        | How                                             | Read |
|------------------|-------------------------------------------------|------|
| **Idle/holding** | `hold` at a fixed angle                          | steady A |
| **Moving**       | `move` slowly across the range                   | A while moving |
| **Stall (peak)** | gently block the output by hand for a moment*    | peak A |

```bash
# Hold at 135 deg for 10 s and read the steady current:
python3 servo_test.py hold --channel 9 --angle 135 --seconds 10 --min 0 --max 270

# Slow move to see current rise under load:
python3 servo_test.py move --channel 9 --start 90 --end 180 \
        --speed 15 --min 0 --max 270
```
\* Stall test: only briefly — stall current is high and heats the servo.
Note the peak, then release:
```bash
python3 servo_test.py release --channels 9
```

Record for each gearbox: holding A, moving A, stall A, and deg/s. That
tells you the per-servo budget and sizes the servo power rail (sum of
simultaneous movers × their moving current, with headroom for stalls).

## 5. Differential gearboxes

For the differential joints, test the two motors **together** so the
gearbox sees realistic combined load:
```bash
python3 servo_test.py diff --a 9 --b 10 --pitch 15 --roll 0   # pure pitch
python3 servo_test.py diff --a 9 --b 10 --pitch 0  --roll 15  # pure roll
```
Watch the PSU current for each mode — differentials can draw more when
both motors oppose each other.

---
For a proper logged current curve later, add an **INA219** on the servo
rail (I²C) and we can have the tool read and plot it automatically.
