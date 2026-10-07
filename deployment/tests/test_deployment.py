import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
checker = load('check-release')
launcher = load('launch')

class ReleaseTests(unittest.TestCase):
    def fixture(self, directory, corrupt=False, machine=183, extra=False):
        elf = bytearray(64)
        elf[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', elf, 18, machine)
        files = {p: bytes(elf) if p in checker.ELFS else b'test' for p in checker.REQUIRED - {'manifest.json'}}
        manifest = {'format': 1, 'architecture': 'arm64', 'os_major': '13',
                    'source_revision': 'a' * 40, 'pd_version': '0.55.2+ds-2',
                    'files': {p: hashlib.sha256(v).hexdigest() for p,v in files.items()}}
        files['manifest.json'] = json.dumps(manifest).encode()
        if corrupt:
            files['patches/acceptance.pd'] += b'changed'
        if extra:
            files['../../escape'] = b'bad'
        path = Path(directory) / 'fixture.tar.gz'
        with tarfile.open(path, 'w:gz') as archive:
            for name, data in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))
        return path
    def test_accepts_valid_container(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(checker.validate(self.fixture(d))['architecture'], 'arm64')
    def test_rejects_corruption_wrong_elf_and_escape(self):
        for options in [{'corrupt': True}, {'machine': 62}, {'extra': True}]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):
                    checker.validate(self.fixture(d, **options))
    def test_rejects_nonregular_member(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.fixture(d)
            with tarfile.open(path, 'r:gz') as archive:
                members = [(m, archive.extractfile(m).read()) for m in archive.getmembers()]
            with tarfile.open(path, 'w:gz') as archive:
                for m,data in members:
                    if m.name == 'bin/launch.py':
                        m.type = tarfile.SYMTYPE
                        m.linkname = '/etc/passwd'
                        m.size = 0
                    archive.addfile(m, io.BytesIO(data))
            with self.assertRaises(ValueError):
                checker.validate(path)

class ChipTests(unittest.TestCase):
    def result(self, path):
        class Result:
            returncode = 0
            stdout = path + ': name=gpiochip0 label=pinctrl-bcm2835 lines=54\n'
        return Result()
    def test_deduplicates_aliases(self):
        with patch.object(launcher.glob, 'glob', return_value=['/dev/gpiochip0','/dev/gpiochip4']), \
             patch.object(launcher.os.path, 'realpath', return_value='/dev/gpiochip0'), \
             patch.object(launcher.os, 'access', return_value=True), \
             patch.object(launcher.subprocess, 'run', return_value=self.result('/dev/gpiochip0')):
            self.assertEqual(launcher.choose_chip('/inspector', 'auto'), '/dev/gpiochip0')
    def test_rejects_ambiguous_controllers(self):
        with patch.object(launcher.glob, 'glob', return_value=['/dev/gpiochip0','/dev/gpiochip1']), \
             patch.object(launcher.os, 'access', return_value=True), \
             patch.object(launcher.subprocess, 'run', side_effect=lambda args, **kw: self.result(args[1])):
            with self.assertRaises(RuntimeError):
                launcher.choose_chip('/inspector', 'auto')
    def test_rejects_wrong_label(self):
        result = self.result('/dev/gpiochip0')
        result.stdout = result.stdout.replace('pinctrl-bcm2835', 'raspberrypi-exp-gpio')
        with patch.object(launcher.os, 'access', return_value=True), \
             patch.object(launcher.subprocess, 'run', return_value=result):
            with self.assertRaises(RuntimeError):
                launcher.choose_chip('/inspector', '/dev/gpiochip0')

if __name__ == '__main__':
    unittest.main()
