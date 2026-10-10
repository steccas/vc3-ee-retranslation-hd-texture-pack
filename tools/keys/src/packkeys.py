# SPDX-License-Identifier: GPL-3.0-or-later
"""Collect all keys known to the efonte pack (ini [hashes] + original dump filenames)."""
import os, re
def load(packdir):
    keys = {}
    for root, _, fs in os.walk(os.path.join(packdir, 'original')):
        for f in fs:
            m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\.png$', f)
            if m: keys.setdefault(m.group(1), set()).add(os.path.relpath(os.path.join(root, f), packdir))
    sec = None
    for line in open(os.path.join(packdir, 'textures.ini'), encoding='utf-8', errors='replace'):
        line = line.strip()
        if line.startswith('['): sec = line; continue
        if sec == '[hashes]':
            m = re.match(r'^([0-9a-f]{24})(?:_\d+)?\s*=\s*(.*)$', line)
            if m: keys.setdefault(m.group(1), set()).add('ini:' + m.group(2))
    return keys
