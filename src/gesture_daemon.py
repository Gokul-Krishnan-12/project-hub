#!/usr/bin/env python3
"""
Touchpad Edge-Swipe Gesture Daemon.
Monitors the touchpad for swipes starting at the right edge and toggles the Command Center.
"""

import os
import sys
import time
import struct
import fcntl
import signal
import argparse
import subprocess
from pathlib import Path

# Event definitions from linux/input.h
EV_SYN = 0x00
EV_KEY = 0x01
EV_ABS = 0x03

SYN_REPORT = 0x00
BTN_TOUCH = 0x14A

ABS_X = 0x00
ABS_Y = 0x01
ABS_MT_SLOT = 0x2F
ABS_MT_POSITION_X = 0x35
ABS_MT_POSITION_Y = 0x36
ABS_MT_TRACKING_ID = 0x39

EVENT_FORMAT = "qqHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

def EVIOCGABS(abs_code):
    return (2 << 30) | (24 << 16) | (ord('E') << 8) | (0x40 + abs_code)

def find_touchpad_device():
    try:
        with open("/proc/bus/input/devices", "r") as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Error reading /proc/bus/input/devices: {e}")
        return None, None

    blocks = content.strip().split("\n\n")
    for block in blocks:
        lines = block.split("\n")
        name = ""
        handlers = ""
        for line in lines:
            if line.startswith("N: Name="):
                name = line.split("=", 1)[1].strip('"')
            elif line.startswith("H: Handlers="):
                handlers = line.split("=", 1)[1]

        if "touchpad" in name.lower():
            for part in handlers.split():
                if part.startswith("event"):
                    return f"/dev/input/{part}", name

    return None, None

def get_abs_range(fd, code):
    buf = bytearray(24)
    try:
        fcntl.ioctl(fd, EVIOCGABS(code), buf)
        value, minimum, maximum, fuzz, flat, res = struct.unpack("iiiiii", buf)
        return minimum, maximum
    except Exception:
        return 0, 0

def toggle_command_center():
    script_path = str(Path(__file__).parent / "main.py")
    try:
        res = subprocess.run(["pgrep", "-f", "(project-hub|touchpad-command-center)/src/main.py"], capture_output=True, text=True)
        pids = [int(p) for p in res.stdout.strip().split() if p.isdigit() and int(p) != os.getpid()]
        if pids:
            print("[*] Project Hub is open. Closing...")
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
            return
    except Exception:
        pass

    print("[*] Launching Project Hub...")
    env = os.environ.copy()
    subprocess.Popen([sys.executable, script_path], env=env)

def run_monitor(test_mode=False):
    dev_path, dev_name = find_touchpad_device()
    if not dev_path:
        print("[!] Touchpad device not found.")
        sys.exit(1)

    print(f"[*] Detected Touchpad: {dev_name} ({dev_path})")

    if not os.access(dev_path, os.R_OK):
        print(f"[!] Access denied to {dev_path}.")
        print("[!] Run: sudo usermod -a -G input $USER")
        print("[!] Then log out and log back in, or run: newgrp input")
        sys.exit(1)

    fd = os.open(dev_path, os.O_RDONLY)

    min_x, max_x = get_abs_range(fd, ABS_MT_POSITION_X)
    if max_x == 0:
        min_x, max_x = get_abs_range(fd, ABS_X)
    if max_x == 0:
        max_x = 3200

    min_y, max_y = get_abs_range(fd, ABS_MT_POSITION_Y)
    if max_y == 0:
        min_y, max_y = get_abs_range(fd, ABS_Y)
    if max_y == 0:
        max_y = 2000

    print(f"[*] Touchpad Range: X=[{min_x}, {max_x}], Y=[{min_y}, {max_y}]")
    edge_x_threshold = max_x - int((max_x - min_x) * 0.18)
    swipe_min_dist = int((max_x - min_x) * 0.12)

    touch_active = False
    start_x = 0
    start_y = 0
    start_time = 0
    started_in_edge = False
    last_trigger = 0

    cur_x = 0
    cur_y = 0

    while True:
        data = os.read(fd, EVENT_SIZE)
        if not data or len(data) < EVENT_SIZE:
            continue

        tv_sec, tv_usec, ev_type, ev_code, ev_value = struct.unpack(EVENT_FORMAT, data)

        if ev_type == EV_ABS:
            if ev_code in (ABS_MT_POSITION_X, ABS_X):
                cur_x = ev_value
            elif ev_code in (ABS_MT_POSITION_Y, ABS_Y):
                cur_y = ev_value
            elif ev_code == ABS_MT_TRACKING_ID:
                if ev_value >= 0:
                    touch_active = True
                    start_x = cur_x
                    start_y = cur_y
                    start_time = time.time()
                    started_in_edge = (cur_x >= edge_x_threshold)
                    if test_mode:
                        print(f"-> Touch at ({cur_x}, {cur_y}) [In Edge: {started_in_edge}]")
                else:
                    touch_active = False
                    started_in_edge = False

        elif ev_type == EV_KEY and ev_code == BTN_TOUCH:
            if ev_value == 1:
                touch_active = True
                start_x = cur_x
                start_y = cur_y
                start_time = time.time()
                started_in_edge = (cur_x >= edge_x_threshold)
            else:
                touch_active = False
                started_in_edge = False

        elif ev_type == EV_SYN and ev_code == SYN_REPORT:
            now = time.time()
            if touch_active and started_in_edge:
                duration = now - start_time
                if duration <= 0.6:
                    distance_left = start_x - cur_x
                    if distance_left >= swipe_min_dist:
                        if (now - last_trigger) > 1.5:
                            last_trigger = now
                            print(f"\n[🔥] RIGHT-EDGE SWIPE DETECTED! Distance: {distance_left} units")
                            toggle_command_center()
                            started_in_edge = False

def main():
    parser = argparse.ArgumentParser(description="Touchpad Gesture Daemon")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--trigger", action="store_true", help="Toggle command center directly")
    args = parser.parse_args()

    if args.trigger:
        toggle_command_center()
        return

    run_monitor(test_mode=args.test)

if __name__ == "__main__":
    main()

