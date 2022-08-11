#!/usr/bin/python

import sys
import mmap
import os
import struct
from pathlib import Path

dumpsdir = sys.argv[1]
base = int(sys.argv[2], 16)

dumps = []

for fname in os.listdir(dumpsdir):
    start, end = fname.split('-')
    start = int(start, 16)
    end = int(end, 16)
    p = Path(dumpsdir + '/' + fname)
    size = p.stat().st_size
    if start + size != end:
        print(f'warn: {start:x} + {size} = {start+size:x} != {end:x}')
        end = start + size
    f = open(p, 'rb')
    dumps.append((start, end, mmap.mmap(f.fileno(), size, prot=mmap.PROT_READ)))

def read(at):
    for start, end, m in dumps:
        if at not in range(start, end):
            continue
        addr = at - start
        bytes_ = m[addr:addr+8]
        return struct.unpack('Q', bytes_)[0]
    return None

def is_block(value):
    return (value & 1) == 0

def as_int(value):
    if is_block(value):
        raise ValueError(f"value at {at} is block")
    return value >> 1

def as_block(value):
    if not is_block(value):
        raise ValueError(f"value at {at} is not block")
    return block(value)

def block(value):
    header = read(value - 8)
    tag = header & 255
    size = header >> 10
    return size, tag

def field(value, n):
    return read(value + n * 8)

def left(base):
    return field(base, 0)

def right(base):
    return field(base, 3)

def value(base):
    return as_int(field(base, 2))

def key(base):
    return as_int(field(base, 1))

def traverse(value):
    if not is_block(value):
        assert as_int(value) == 0
        return []
    return [*traverse(left(value)), chr(as_int(field(value, 2))), *traverse(right(value))]
