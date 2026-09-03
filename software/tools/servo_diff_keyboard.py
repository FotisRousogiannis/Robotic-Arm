#!/usr/bin/env python3
"""Keyboard teleop for a DIFFERENTIAL pair of continuous-rotation servos.

The base (and wrist) use a differential: two servos combine to make two
motions.

    PITCH  -> both servos spin the SAME direction
    ROLL   -> both servos spin OPPOSITE directions

Motor speeds:
    speed_A = pitch + roll
    speed_B = pitch - roll   (each clamped to -1..1, then -> pulse)

Keys (HOLD to move, release to stop)
------------------------------------
    w / s   pitch up / down     (both servos together)
    a / d   roll left / right   (servos opposed)
    + / -   change speed magnitude
    space   stop both
    q       quit

Also accepts the Greek keyboard layout (ς/σ/α/δ map to w/s/a/d).

Each servo has its own neutral pulse — calibrate first with servo_test.py
(pulse) and pass --center-a / --center-b. If a motion goes the wrong way,
flip that motor with --invert-a / --invert-b.

Run on the Pi (venv active), e.g.:
    python3 servo_diff_keyboard.py --a 0 --b 1 \
            --center-a 1600 --center-b 1600 --min_us 500 --max_us 2500
"""

from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty

from servo_test import Driver, speed_to_pulse
from servo_keyboard import normalize_key

# roll/pitch use w s a d; also accept + / - and space/q
EXTRA = {'ς': 'w', 'σ': 's', 'α': 'a', 'δ': 'd'}


def norm(k: str) -> str:
    return normalize_key(EXTRA.get(k, k))


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', type=int, default=0, help='motor A channel')
    ap.add_argument('--b', type=int, default=1, help='motor B channel')
    ap.add_argument('--address', type=lambda x: int(x, 0), default=0x40)
    ap.add_argument('--center-a', type=float, default=1600.0)
    ap.add_argument('--center-b', type=float, default=1600.0)
    ap.add_argument('--min_us', type=float, default=500.0)
    ap.add_argument('--max_us', type=float, default=2500.0)
    ap.add_argument('--invert-a', action='store_true', help='flip motor A direction')
    ap.add_argument('--invert-b', action='store_true', help='flip motor B direction')
    ap.add_argument('--speed', type=float, default=0.4, help='speed magnitude 0..1')
    ap.add_argument('--step', type=float, default=0.1)
    ap.add_argument('--hold-timeout', type=float, default=0.25)
    args = ap.parse_args(argv)

    if not sys.stdin.isatty():
        print('Needs an interactive terminal (real TTY over SSH).')
        return 1

    drv = Driver(address=args.address)
    ca, cb = args.a, args.b
    sign_a = -1.0 if args.invert_a else 1.0
    sign_b = -1.0 if args.invert_b else 1.0
    mag = clamp(args.speed, 0.0, 1.0)

    def drive(pitch, roll):
        sa = clamp(pitch + roll)
        sb = clamp(pitch - roll)
        drv.set_pulse_us(ca, speed_to_pulse(sign_a * sa, args.center_a,
                                            args.min_us, args.max_us))
        drv.set_pulse_us(cb, speed_to_pulse(sign_b * sb, args.center_b,
                                            args.min_us, args.max_us))
        label = ('PITCH+' if pitch > 0 else 'PITCH-' if pitch < 0 else
                 'ROLL+' if roll > 0 else 'ROLL-' if roll < 0 else 'STOP')
        print(f'\r {label:7} mag={mag:.2f}  A(ch{ca})={sa:+.2f} '
              f'B(ch{cb})={sb:+.2f}   ', end='', flush=True)

    print(__doc__)
    print(f'--- base differential A=ch{ca} B=ch{cb} — HOLD w/s/a/d, q to quit ---')
    drive(0, 0)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    pitch = roll = 0.0
    last_move = 0.0
    moving = False
    try:
        tty.setraw(fd)
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            now = time.time()
            if r:
                k = norm(sys.stdin.read(1))
                if k == 'q' or k == '\x03':
                    break
                elif k == 'w':
                    pitch, roll = mag, 0.0; moving = True; last_move = now
                elif k == 's':
                    pitch, roll = -mag, 0.0; moving = True; last_move = now
                elif k == 'a':
                    pitch, roll = 0.0, -mag; moving = True; last_move = now
                elif k == 'd':
                    pitch, roll = 0.0, mag; moving = True; last_move = now
                elif k in ('+', '='):
                    mag = clamp(mag + args.step, 0.0, 1.0)
                elif k in ('-', '_'):
                    mag = clamp(mag - args.step, 0.0, 1.0)
                elif k == ' ':
                    pitch = roll = 0.0; moving = False
                drive(pitch, roll)
            if moving and (now - last_move) > args.hold_timeout:
                pitch = roll = 0.0
                moving = False
                drive(0, 0)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        drive(0, 0)   # centers = stop
        print('\nstopped. bye.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
