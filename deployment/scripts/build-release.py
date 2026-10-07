#!/usr/bin/env python3
"""Build on a separate ARM64 Debian 13 builder, never during provisioning."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def main():
    if platform.machine() != 'aarch64' or run('dpkg', '--print-architecture') != 'arm64':
        sys.exit('Release builds require an ARM64 Debian 13 builder.')
    os_release = Path('/etc/os-release').read_text()
    if 'VERSION_ID="13"' not in os_release or 'ID=debian' not in os_release:
        sys.exit('Release builds require Debian 13 (Trixie).')
    if run('git', '-C', str(ROOT), 'status', '--porcelain'):
        sys.exit('Commit changes before building a release; the source tree must be clean.')
    revision = run('git', '-C', str(ROOT), 'rev-parse', 'HEAD')
    epoch = int(run('git', '-C', str(ROOT), 'show', '-s', '--format=%ct', 'HEAD'))
    pd_version = run('dpkg-query', '-W', '-f=${Version}', 'puredata-core')
    dev_version = run('dpkg-query', '-W', '-f=${Version}', 'puredata-dev')
    if pd_version != dev_version:
        sys.exit('puredata-core and puredata-dev versions must match.')
    externals = ROOT / 'software/externals'
    subprocess.run(['make', '-C', str(externals), 'clean'], check=True)
    subprocess.run(['make', '-C', str(externals), 'all', 'check', 'CC=cc', f'CFLAGS=-O2 -g -ffile-prefix-map={ROOT}=.'], check=True)
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    output = destination / f'terminal_tedium-{revision[:12]}-arm64.tar.gz'
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary)
        (stage / 'externals').mkdir()
        (stage / 'bin').mkdir()
        (stage / 'patches').mkdir()
        for name in ['terminal_tedium_adc.pd_linux', 'tedium_input.pd_linux',
                     'tedium_output.pd_linux', 'tedium_switch.pd_linux', 'libtt_gpio.so']:
            shutil.copy2(externals / 'build' / name, stage / 'externals' / name)
        shutil.copy2(externals / 'build/tt_gpio_inspect', stage / 'bin/tt_gpio_inspect')
        shutil.copy2(ROOT / 'deployment/scripts/launch.py', stage / 'bin/launch.py')
        shutil.copy2(ROOT / 'software/acceptance/acceptance.pd', stage / 'patches/acceptance.pd')
        files = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(stage.rglob('*')) if p.is_file()}
        manifest = {'format': 1, 'architecture': 'arm64', 'os_major': '13',
                    'source_revision': revision, 'pd_version': pd_version,
                    'compiler': run('cc', '--version').splitlines()[0], 'files': files}
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        # Fixed timestamps, owners and gzip header make identical inputs repeatable.
        import gzip
        with output.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode='w') as archive:
                for p in sorted(stage.rglob('*')):
                    if not p.is_file():
                        continue
                    info = archive.gettarinfo(str(p), str(p.relative_to(stage)))
                    info.uid = info.gid = 0
                    info.uname = info.gname = ''
                    info.mtime = epoch
                    info.mode = 0o755 if info.name == 'bin/tt_gpio_inspect' else 0o644
                    with p.open('rb') as stream:
                        archive.addfile(info, stream)
    subprocess.run([sys.executable, str(ROOT / 'deployment/scripts/check-release.py'), str(output)], check=True)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + '.sha256').write_text(f'{checksum}  {output.name}\n')
    print(output)
    print('SHA256=' + checksum)

if __name__ == '__main__':
    main()
