#!/usr/bin/env python3

import subprocess
import sys
import numpy as np
from PIL import Image

def adb_shell(cmd):
    result = subprocess.run(['adb', 'shell'] + cmd, capture_output=True, text=True)
    return result.stdout.strip()

def adb_exec_out(cmd):
    result = subprocess.run(['adb', 'exec-out'] + cmd, capture_output=True)
    return result.stdout

def shot():
    virtual = adb_shell(['cat', '/sys/class/graphics/fb0/virtual_size'])
    vwidth, vheight = map(int, virtual.split(','))

    mode_line = adb_shell(['cat', '/sys/class/graphics/fb0/modes']).splitlines()[0]
    import re
    match = re.search(r'(\d+)x(\d+)', mode_line)
    if not match:
        sys.exit(1)
    pwidth, pheight = map(int, match.groups())

    xoffset = (vwidth - pwidth) // 2
    yoffset = 0

    bpp = int(adb_shell(['cat', '/sys/class/graphics/fb0/bits_per_pixel']))
    bytes_per_pixel = bpp // 8

    fb_data = adb_exec_out(['cat', '/dev/fb0'])

    arr = np.frombuffer(fb_data, dtype=np.uint8).reshape((vheight, vwidth, bytes_per_pixel))

    if bytes_per_pixel == 4:
        fbset = adb_shell(['fbset'])
        if "rgba" in fbset.lower():
            order = [0, 1, 2, 3]
        elif "argb" in fbset.lower():
            order = [1, 2, 3, 0]
        elif "bgra" in fbset.lower():
            order = [2, 1, 0, 3]
        elif "abgr" in fbset.lower():
            order = [3, 2, 1, 0]
        else:
            order = [0, 1, 2, 3]
        arr = arr[..., order]
    elif bytes_per_pixel == 3:
        arr = arr[..., :3]

    cropped = arr[yoffset:yoffset+pheight, xoffset:xoffset+pwidth]

    mode = 'RGBA' if bytes_per_pixel == 4 else 'RGB'
    img = Image.fromarray(cropped, mode=mode)
    return img
