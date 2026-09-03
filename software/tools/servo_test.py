#!/usr/bin/env python3
"""Standalone servo / gearbox test tool for the robotic arm.

No ROS required — runs directly on the Raspberry Pi (or any machine) to
exercise individual servos and the differential mechanisms so you can
verify the wrist and its gearboxes before committing to the full stack.

If the PCA9685 libraries are not installed (e.g. on a laptop) the tool
runs in SIMULATION mode and just prints the pulses it would send.

Install on the Pi (once):
    pip install adafruit-circuitpython-pca9685 adafruit-blinka
    # and enable I2C via raspi-config

Examples
--------
# Move channel 9 to 135 deg (its center):
    python3 servo_test.py set --channel 9 --angle 135

# Slowly sweep channel 9 between 120-150 deg and back (watch the gearbox).
# --min/--max are the servo's FULL calibrated range; --start/--end the
# safe sub-range to sweep:
    python3 servo_test.py sweep --channel 9 --min 0 --max 270 \
            --start 120 --end 150 --step 2

# Center all wrist channels:
    python3 servo_test.py center --channels 8 9 10 11

# Test the wrist DIFFERENTIAL: pure pitch, then pure roll:
    python3 servo_test.py diff --a 9 --b 10 --pitch 20 --roll 0
    python3 servo_test.py diff --a 9 --b 10 --pitch 0  --roll 20

# Release (stop holding) channels:
    python3 servo_test.py release --channels 9 10

SAFETY: start with small angles and low travel. Keep a hand near the
power switch. Differential gearboxes can bind — stop immediately if a
servo stalls or buzzes.
"""

from __future__ import annotations

import argparse
import sys
import time

# Default pulse-width calibration (microseconds) at the servo extremes.
PULSE_MIN_US = 500.0
PULSE_MAX_US = 2500.0
ANGLE_MIN = 0.0
ANGLE_MAX = 270.0   # GXservo 270deg on the wrist; use 180 for 180deg servos
PWM_FREQ = 50


class Driver:
    """PCA9685 driver with a simulation fallback."""

    def __init__(self, address=0x40, frequency=PWM_FREQ):
        self.frequency = frequency
        self.sim = False
        self.pca = None
        try:
            from board import SCL, SDA
            import busio
            from adafruit_pca9685 import PCA9685

            i2c = busio.I2C(SCL, SDA)
            self.pca = PCA9685(i2c, address=address)
            self.pca.frequency = frequency
            print(f'PCA9685 ready @ 0x{address:02x}, {frequency} Hz')
        except Exception as exc:  # noqa: BLE001
            self.sim = True
            print(f'[SIMULATION] PCA9685 unavailable ({exc}).')

    def set_pulse_us(self, channel: int, pulse_us: float) -> None:
        if self.sim or self.pca is None:
            print(f'  [sim] ch{channel:>2} <- {pulse_us:6.0f} us')
            return
        period_us = 1_000_000.0 / self.frequency
        duty = int(max(0.0, min(1.0, pulse_us / period_us)) * 0xFFFF)
        self.pca.channels[channel].duty_cycle = duty

    def release(self, channel: int) -> None:
        """Stop driving the channel (servo goes slack)."""
        if self.sim or self.pca is None:
            print(f'  [sim] ch{channel:>2} released')
            return
        self.pca.channels[channel].duty_cycle = 0


def angle_to_pulse(angle, a_min=ANGLE_MIN, a_max=ANGLE_MAX,
                   p_min=PULSE_MIN_US, p_max=PULSE_MAX_US):
    span = a_max - a_min
    clamped = max(a_min, min(a_max, angle))
    frac = 0.0 if span == 0 else (clamped - a_min) / span
    return p_min + frac * (p_max - p_min)


def cmd_set(drv, args):
    print(f'set ch{args.channel} -> {args.angle} deg')
    drv.set_pulse_us(args.channel, angle_to_pulse(
        args.angle, args.min, args.max))


def cmd_sweep(drv, args):
    start = args.start if args.start is not None else args.min
    end = args.end if args.end is not None else args.max
    print(f'sweep ch{args.channel}: {start} -> {end} deg '
          f'(servo range {args.min}..{args.max}), '
          f'step {args.step}, dwell {args.dwell}s')
    seq = list(_frange(start, end, args.step))
    seq += list(reversed(seq))
    for angle in seq:
        drv.set_pulse_us(args.channel, angle_to_pulse(angle, args.min, args.max))
        print(f'  {angle:6.1f} deg')
        time.sleep(args.dwell)


def cmd_center(drv, args):
    for ch in args.channels:
        mid = (args.min + args.max) / 2.0
        print(f'center ch{ch} -> {mid} deg')
        drv.set_pulse_us(ch, angle_to_pulse(mid, args.min, args.max))


def cmd_diff(drv, args):
    """Differential mixing test: two servos -> pitch + roll."""
    a = args.center + args.pitch + args.roll
    b = args.center + args.pitch - args.roll
    print(f'diff pitch={args.pitch} roll={args.roll} '
          f'-> ch{args.a}={a:.1f} deg, ch{args.b}={b:.1f} deg')
    drv.set_pulse_us(args.a, angle_to_pulse(a, args.min, args.max))
    drv.set_pulse_us(args.b, angle_to_pulse(b, args.min, args.max))


def cmd_move(drv, args):
    """Move at a controlled rate (deg/s) and report the timing.

    Useful for measuring speed and, held at the end, current draw on the
    bench PSU. Interpolates from --start to --end at ~--speed deg/s.
    """
    start = args.start if args.start is not None else (args.min + args.max) / 2
    end = args.end
    speed = max(1e-3, args.speed)
    dt = args.dt
    step = speed * dt
    print(f'move ch{args.channel}: {start} -> {end} deg at {speed} deg/s '
          f'(servo range {args.min}..{args.max})')
    t0 = time.time()
    for angle in _frange(start, end, step):
        drv.set_pulse_us(args.channel, angle_to_pulse(angle, args.min, args.max))
        time.sleep(dt)
    drv.set_pulse_us(args.channel, angle_to_pulse(end, args.min, args.max))
    elapsed = time.time() - t0
    travel = abs(end - start)
    eff = travel / elapsed if elapsed > 0 else 0.0
    print(f'  done: {travel:.1f} deg in {elapsed:.2f} s '
          f'-> {eff:.1f} deg/s effective')
    print('  >> read CURRENT (A) on your PSU display now while it holds <<')


def cmd_hold(drv, args):
    """Drive to an angle and hold, so you can read current on the PSU."""
    print(f'hold ch{args.channel} -> {args.angle} deg for {args.seconds}s')
    drv.set_pulse_us(args.channel, angle_to_pulse(args.angle, args.min, args.max))
    print('  >> read CURRENT (A) on your PSU display now <<')
    time.sleep(args.seconds)
    if args.release:
        drv.release(args.channel)
        print('  released')


def cmd_release(drv, args):
    for ch in args.channels:
        drv.release(ch)


def _frange(start, stop, step):
    step = abs(step) or 1.0
    if stop < start:
        step = -step
    x = start
    while (step > 0 and x <= stop) or (step < 0 and x >= stop):
        yield round(x, 3)
        x += step


def build_parser():
    # Common options accepted by every subcommand (before or after it).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--address', type=lambda x: int(x, 0), default=0x40)
    common.add_argument('--min', type=float, default=ANGLE_MIN, help='servo min angle')
    common.add_argument('--max', type=float, default=ANGLE_MAX, help='servo max angle')

    p = argparse.ArgumentParser(
        description=__doc__, parents=[common],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('set', parents=[common], help='move one channel to an angle')
    s.add_argument('--channel', type=int, required=True)
    s.add_argument('--angle', type=float, required=True)
    s.set_defaults(func=cmd_set)

    s = sub.add_parser('sweep', parents=[common], help='sweep one channel back and forth')
    s.add_argument('--channel', type=int, required=True)
    s.add_argument('--start', type=float, default=None, help='sweep from (default: --min)')
    s.add_argument('--end', type=float, default=None, help='sweep to (default: --max)')
    s.add_argument('--step', type=float, default=2.0)
    s.add_argument('--dwell', type=float, default=0.05, help='seconds per step')
    s.set_defaults(func=cmd_sweep)

    s = sub.add_parser('center', parents=[common], help='center one or more channels')
    s.add_argument('--channels', type=int, nargs='+', required=True)
    s.set_defaults(func=cmd_center)

    s = sub.add_parser('diff', parents=[common], help='differential mixing test (pitch + roll)')
    s.add_argument('--a', type=int, required=True, help='motor A channel')
    s.add_argument('--b', type=int, required=True, help='motor B channel')
    s.add_argument('--pitch', type=float, default=0.0)
    s.add_argument('--roll', type=float, default=0.0)
    s.add_argument('--center', type=float, default=135.0, help='servo center angle')
    s.set_defaults(func=cmd_diff)

    s = sub.add_parser('move', parents=[common],
                       help='move at a controlled speed (deg/s), timed')
    s.add_argument('--channel', type=int, required=True)
    s.add_argument('--start', type=float, default=None, help='default: mid-range')
    s.add_argument('--end', type=float, required=True)
    s.add_argument('--speed', type=float, default=30.0, help='deg/s')
    s.add_argument('--dt', type=float, default=0.02, help='update period (s)')
    s.set_defaults(func=cmd_move)

    s = sub.add_parser('hold', parents=[common],
                       help='hold an angle so you can read PSU current')
    s.add_argument('--channel', type=int, required=True)
    s.add_argument('--angle', type=float, required=True)
    s.add_argument('--seconds', type=float, default=5.0)
    s.add_argument('--release', action='store_true', help='release after holding')
    s.set_defaults(func=cmd_hold)

    s = sub.add_parser('release', parents=[common], help='stop driving channels (go slack)')
    s.add_argument('--channels', type=int, nargs='+', required=True)
    s.set_defaults(func=cmd_release)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    drv = Driver(address=args.address)
    try:
        args.func(drv, args)
    except KeyboardInterrupt:
        print('\ninterrupted')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
