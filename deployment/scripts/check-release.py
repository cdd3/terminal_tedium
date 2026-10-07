#!/usr/bin/env python3
"""Validate a release without loading target binaries or extracting a tar."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import tarfile

ELFS = {'externals/' + x for x in ['terminal_tedium_adc.pd_linux', 'tedium_input.pd_linux',
        'tedium_output.pd_linux', 'tedium_switch.pd_linux', 'libtt_gpio.so']} | {'bin/tt_gpio_inspect'}
REQUIRED = ELFS | {'bin/launch.py', 'patches/acceptance.pd', 'manifest.json'}

def validate(path):
    with tarfile.open(path, 'r:gz') as archive:
        members = archive.getmembers()
        if len(members) != len(REQUIRED) or {m.name for m in members} != REQUIRED:
            raise ValueError('Unexpected, duplicate, or missing archive members')
        if any(not m.isfile() or m.size > 16 * 1024 * 1024 for m in members):
            raise ValueError('Only bounded regular files are allowed')
        content = {m.name: archive.extractfile(m).read() for m in members}
    manifest = json.loads(content['manifest.json'])
    if (manifest.get('format'), manifest.get('architecture'), manifest.get('os_major')) != (1, 'arm64', '13'):
        raise ValueError('Unsupported release format or target')
    if not re.fullmatch('[0-9a-f]{40}', manifest.get('source_revision', '')):
        raise ValueError('Missing source commit')
    if not isinstance(manifest.get('pd_version'), str) or not manifest['pd_version']:
        raise ValueError('Missing Pd package version')
    if set(manifest['files']) != REQUIRED - {'manifest.json'}:
        raise ValueError('Manifest file set does not match the archive')
    for name, digest in manifest['files'].items():
        if hashlib.sha256(content[name]).hexdigest() != digest:
            raise ValueError('Checksum mismatch: ' + name)
    for name in ELFS:
        data = content[name]
        if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', data, 18)[0] != 183:
            raise ValueError('Expected little-endian AArch64 ELF: ' + name)
    return manifest

if __name__ == '__main__':
    try:
        result = validate(Path(sys.argv[1]))
        print(json.dumps(result))
    except (ValueError, KeyError, IndexError, OSError, tarfile.TarError) as error:
        sys.exit(str(error))
