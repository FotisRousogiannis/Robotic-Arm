#!/usr/bin/env python3
"""Interactive keyboard teleop for a CONTINUOUS-rotation servo.

Drive one continuous servo live from the keyboard over SSH — great for
feeling out a gearbox's speed and watching current on the PSU.

Keys
----
    a / d   spin left (CCW) / right (CW)
    w / s   speed up / slow down (steps)
    space   stop (center pulse)
    r       release (servo goes slack)
    q       quit (stops the servo first)

Speed is a "ladder": w/s change the magnitude in fixed steps; a/d pick the
direction and start moving. The current pulse is shown live.

Run on the Pi (with the venv active):
    python3 servo_keyboard.py --channel 0

Continuous-servo pulse mapping (override if your servo differs):
    --center 1500  --min_us 1000  --max_us 2000
"""

from __future__ import annotations

import argparse
import sys
import termios
import tty

# Reuse the driver + mapping from the main bench tool.
from servo_test import Driver, speed_to_pulse, CONT_CENTER_US, CONT_MIN_US, CONT_MAX_US


def getch() -> str:
    """Read a single keypress (no Enter needed)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--channel', type=int, default=0)
    ap.add_argument('--address', type=lambda x: int(x, 0), default=0x40)
    ap.add_argument('--center', type=float, default=CONT_CENTER_US)
    ap.add_argument('--min_us', type=float, default=CONT_MIN_US)
    ap.add_argument('--max_us', type=float, default=CONT_MAX_US)
    ap.add_argument('--step', type=float, default=0.1, help='speed step per w/s')
    ap.add_argument('--start-speed', type=float, default=0.3,
                    help='initial speed magnitude (0..1)')
    args = ap.parse_args(argv)

    if not sys.stdin.isatty():
        print('This tool needs an interactive terminal (a real TTY over SSH).\n'
              'Run it directly, not through a pipe. For scripted control use '
              'servo_test.py (spin/pulse/stop).')
        return 1

    drv = Driver(address=args.address)
    ch = args.channel
    mag = max(0.0, min(1.0, args.start_speed))
    direction = 0        # -1 = CCW (a), +1 = CW (d), 0 = stopped

    def apply():
        speed = direction * mag
        pulse = speed_to_pulse(speed, args.center, args.min_us, args.max_us)
        drv.set_pulse_us(ch, pulse)
        arrow = {-1: 'CCW <', 0: 'STOP', 1: '> CW'}[direction]
        bar = '#' * int(mag * 20)
        print(f'\r ch{ch}  {arrow:5}  speed={speed:+.2f}  {pulse:6.0f}us  '
              f'[{bar:<20}]   ', end='', flush=True)

    print(__doc__)
    print(f'--- controlling channel {ch} — press keys (q to quit) ---')
    drv.set_pulse_us(ch, args.center)  # start stopped
    apply()
    try:
        while True:
            k = getch().lower()
            if k == 'q':
                break
            elif k == 'a':
                direction = -1
            elif k == 'd':
                direction = 1
            elif k == 'w':
                mag = min(1.0, mag + args.step)
            elif k == 's':
                mag = max(0.0, mag - args.step)
            elif k == ' ':
                direction = 0
            elif k == 'r':
                drv.release(ch)
                print('\n  released (servo slack) — press a/d to drive again')
                continue
            else:
                continue
            apply()
    except KeyboardInterrupt:
        pass
    finally:
        drv.set_pulse_us(ch, args.center)   # always stop on exit
        print('\nstopped. bye.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
