#!/usr/bin/env python3
"""Wait for and validate appliance devices, restore routing, then exec Pd."""
import glob
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

MIXER = [('Master', '121'), ('Capture', '23'), ('Input Mux', 'Line In'),
         ('Line', 'cap'), ('Mic', 'nocap'), ('Output Mixer HiFi', 'on'),
         ('Output Mixer Line Bypass', 'off'), ('Output Mixer Mic Sidetone', 'off')]

def choose_chip(inspector, configured):
    paths = [configured] if configured != 'auto' else glob.glob('/dev/gpiochip*')
    matches = set()
    for path in paths:
        resolved = os.path.realpath(path)
        if not os.access(resolved, os.R_OK | os.W_OK):
            continue
        result = subprocess.run([str(inspector), resolved], text=True, capture_output=True)
        if result.returncode == 0 and re.search(r'\blabel=pinctrl-bcm2835 lines=54\b', result.stdout):
            matches.add(resolved)
    if len(matches) != 1:
        raise RuntimeError('Expected one accessible pinctrl-bcm2835 GPIO controller: ' + repr(matches))
    return matches.pop()

def main():
    config = json.loads(Path(sys.argv[1]).read_text())
    root = Path(__file__).resolve().parents[1]
    card = 'sndrpiproto'
    deadline = time.monotonic() + 30
    while True:
        try:
            if not re.search(r'\[' + card + r'\s*\]', Path('/proc/asound/cards').read_text()):
                raise RuntimeError('WM8731 ALSA card not registered')
            if not os.access('/dev/spidev0.1', os.R_OK | os.W_OK):
                raise RuntimeError('SPI device missing or inaccessible')
            chip = choose_chip(root / 'bin/tt_gpio_inspect', config['gpio_chip'])
            break
        except (RuntimeError, OSError) as error:
            if time.monotonic() >= deadline:
                raise RuntimeError('Hardware readiness timeout: ' + str(error)) from error
            time.sleep(0.5)
    for control, value in MIXER:
        subprocess.run(['/usr/bin/amixer', '-q', '-c', card, 'sset', control, value], check=True)
    patch = root / 'patches/acceptance.pd'
    if not patch.is_file():
        raise RuntimeError('Acceptance patch missing')
    os.environ['TT_GPIO_CHIP'] = chip
    # -alsaadd exposes a named PCM; -audioadddev selects that exact name,
    # independent of card index. Verified against Pd 0.55-2 s_main/s_audio_alsa.
    pcm = 'hw:CARD=sndrpiproto,DEV=0'
    args = ['/usr/bin/pd', '-noprefs', '-nogui', '-stderr', '-nrt', '-nomidi',
            '-alsa', '-alsaadd', pcm, '-audioadddev', pcm,
            '-inchannels', '2', '-outchannels', '2', '-r', '48000', '-audiobuf', '50',
            '-path', str(root / 'externals'), str(patch)]
    os.chdir('/var/lib/terminal_tedium')
    print('TT_START: GPIO=' + chip + ' PCM=' + pcm + ' patch=' + str(patch), flush=True)
    os.execv(args[0], args)

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit('TT_START_FAILED: ' + str(error))
