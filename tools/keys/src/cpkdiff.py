#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""List files whose decompressed content differs between two CPKs."""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cpk
a, b = cpk.CPK(sys.argv[1]), cpk.CPK(sys.argv[2])
A = {e['name']: e for e in a.entries}; B = {e['name']: e for e in b.entries}
ch = [n for n in sorted(set(A) & set(B)) if hashlib.md5(a.read(A[n])).digest() != hashlib.md5(b.read(B[n])).digest()]
ch += sorted(set(A) ^ set(B))
open(sys.argv[3], 'w').write('\n'.join(ch)); print(len(ch), 'changed files')
