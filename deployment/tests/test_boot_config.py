"""Exercise the actual Ansible firmware tasks on a temporary file twice."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import yaml

DEPLOYMENT = Path(__file__).resolve().parents[1]
ANSIBLE = shutil.which('ansible-playbook')

@unittest.skipUnless(ANSIBLE, 'ansible-playbook is not installed')
class BootConfigTests(unittest.TestCase):
    def test_preservation_normalization_and_second_run(self):
        fixture = '# untouched\ndtparam=audio=on\ndtparam=spi=on\ndtoverlay=proto-codec\n[pi5]\ndtoverlay=nospi10\n[all]\nenable_uart=1\n'
        source = yaml.safe_load((DEPLOYMENT / 'provision.yml').read_text())[0]
        names = ['Read firmware configuration', 'Preserve unrelated firmware settings and normalize owned directives',
                 'Enable the tested codec and SPI configuration']
        tasks = [dict(t) for t in source['tasks'] if t.get('name') in names]
        for task in tasks:
            task.pop('notify', None)
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            config = directory / 'config.txt'
            config.write_text(fixture)
            play = {'hosts': 'localhost', 'gather_facts': False,
                    'vars': {'tt_boot_config': str(config), 'tt_boot_begin': source['vars']['tt_boot_begin'],
                             'tt_boot_end': source['vars']['tt_boot_end']}, 'tasks': tasks}
            playfile = directory / 'test.yml'
            playfile.write_text(yaml.safe_dump([play], sort_keys=False))
            command = [ANSIBLE, '-i', 'localhost,', '-c', 'local', str(playfile)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            once = config.read_text()
            self.assertIn('# untouched\n', once)
            self.assertIn('[pi5]\ndtoverlay=nospi10\n[all]\nenable_uart=1', once)
            self.assertEqual(once.count('dtoverlay=proto-codec'), 1)
            self.assertNotIn('dtparam=audio=on', once)
            self.assertIn('[all]\ndtparam=audio=off\ndtparam=spi=on\ndtoverlay=proto-codec', once)
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertEqual(config.read_text(), once)
            self.assertIn('changed=0', second.stdout)

if __name__ == '__main__':
    unittest.main()
