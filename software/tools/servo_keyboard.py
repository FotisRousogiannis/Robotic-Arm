#!/usr/bin/env python3
"""Interactive keyboard teleop for a CONTINUOUS-rotation servo.

Drive one continuous servo live from the keyboard over SSH — great for
feeling out a gearbox's speed and watching current on the PSU.

Keys
----
    a / d   HOLD to spin left (CCW) / right (CW) — release to STOP
    w / s   speed up / slow down (steps)
    [ / ]   trim the stop pulse down / up (CALIBRATE the neutral)
    space   force stop
    q       quit (stops the servo first)

FIRST TIME: if the servo creeps while idle, tap [ or ] until it sits
perfectly still — that finds this servo's true neutral. Note the shown
center value and pass it next time as --center.

Hold-to-move: the servo turns only WHILE a or d is held down; the moment
you let go it stops (the signal is cut). w/s set the speed magnitude (a
"ladder"). The current pulse is shown live.

Stopping sends the center pulse (--center, default 1500us). This servo
holds still at center and SPINS when the signal is cut, so we never
release it. If it still creeps at center, tune --center.

Run on the Pi (with the venv active):
    python3 servo_keyboard.py --channel 0

Continuous-servo pulse mapping (override if your servo differs):
    --center 1500  --min_us 1000  --max_us 2000
"""

from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty

# Reuse the driver + mapping from the main bench tool.
from servo_test import Driver, speed_to_pulse, CONT_CENTER_US, CONT_MIN_US, CONT_MAX_US


# Greek keyboard layout sends different characters for the same physical
# keys (a->α, d->δ, w->ς, s->σ, q->;). Map them back so the controls work
# whatever the active layout is.
GREEK_TO_LATIN = {
    'α': 'a', 'Α': 'a',
    'δ': 'd', 'Δ': 'd',
    'ς': 'w', 'σ': 's', 'Σ': 's',
    ';': 'q', '·': 'q',
}


def normalize_key(k: str) -> str:
    return GREEK_TO_LATIN.get(k, k).lower()


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
    ap.add_argument('--hold-timeout', type=float, default=0.25,
                    help='hold mode: stop this many seconds after a/d released')
    ap.add_argument('--toggle', action='store_true',
                    help='toggle mode (terminal-friendly): tap a/d to start '
                         'moving, tap space to stop — no key-hold needed')
    ap.add_argument('--trim', type=float, default=5.0,
                    help='microseconds per [ / ] center-trim keypress')
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
              f'center={args.center:.0f}us  [{bar:<20}]   ', end='', flush=True)

    def stop():
        # This servo holds still at the center pulse (verified: 1500us = stop)
        # and SPINS when the signal is cut. So stop = send the center pulse,
        # never release. Tune --center if it still creeps.
        drv.set_pulse_us(ch, args.center)

    print(__doc__)
    mode_help = ('TAP a/d to move, space to stop' if args.toggle
                 else 'HOLD a/d to move, release to stop')
    print(f'--- channel {ch} [{ "toggle" if args.toggle else "hold" } mode]: '
          f'{mode_help} (q to quit) ---')
    stop()
    apply()

    # Hold-to-move: while a/d auto-repeats (key held), keep spinning; once the
    # repeats stop (key released), a short timeout stops the servo.
    hold_timeout = args.hold_timeout
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    moving = False
    last_move = 0.0
    try:
        tty.setraw(fd)
        while True:
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            now = time.time()
            if r:
                k = normalize_key(sys.stdin.read(1))
                if k == 'q' or k == '\x03':      # q or Ctrl+C
                    break
                elif k == 'a':
                    direction = -1; last_move = now; moving = True; apply()
                elif k == 'd':
                    direction = 1; last_move = now; moving = True; apply()
                elif k == 'w':
                    mag = min(1.0, mag + args.step); apply()
                elif k == 's':
                    mag = max(0.0, mag - args.step); apply()
                elif k == '[':                    # trim center down
                    args.center -= args.trim
                    if not moving:
                        stop()
                    apply()
                elif k == ']':                    # trim center up
                    args.center += args.trim
                    if not moving:
                        stop()
                    apply()
                elif k == ' ':
                    moving = False; direction = 0; stop(); apply()
            # Hold mode only: no a/d repeat for a moment -> released -> stop.
            if not args.toggle and moving and (now - last_move) > hold_timeout:
                moving = False
                direction = 0
                stop()
                apply()
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        stop()
        print('\nstopped. bye.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
