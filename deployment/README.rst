Terminal Tedium: Debian 13 ARM64 acceptance appliance
===================================================

Purpose and status
------------------

This is the first clean-card provisioning implementation for a Raspberry Pi
3B+ with the WM8731 Terminal Tedium board. It installs one self-contained
acceptance patch supplied by this repository and starts it through systemd.
It does not load the experimental startup selector, the ``pd`` repository,
third-party Pd libraries, or USB media.

The prototype externals were compiled and tested on the user's ARM64 unit:
stereo audio, all six ADC controls, three buttons, four digital inputs,
and both output jacks and their LEDs worked. The new complete deployment
still requires an external ARM64 release build and fresh-card acceptance.
These are separate claims: prior prototype hardware success does not certify
this playbook, launcher, or bundled patch on a fresh card.

Initial scope is deliberately limited to this board and Pi model. Input
polling detects sampled high-to-low transitions; short pulses may be missed.
Button hold values count nominal 1 ms polling ticks, not wall-clock duration.
No real-time scheduling or low-latency performance guarantee is made.

Bootstrap the OS
----------------

Use a spare card with a functional 64-bit Debian 13 Raspberry Pi base OS,
the Raspberry Pi firmware/kernel and ``proto-codec`` overlay, SSH, Python 3,
a sudo-capable administrator, and working provisioning networking. The
base OS is an input to this workflow; this project does not build an OS image.
Record its filename, download source and SHA256 before flashing, and retain
that image. The exact source image of the current working card has not yet
been established. Consequently an identical whole-card reconstruction is
not yet claimed.

The tested existing unit reported Debian 13 (Trixie), ARM64, kernel
``6.18.50+rpt-rpi-v8`` and Pd ``0.55.2+ds-2``. Do not copy the repository's
historical ``software/config.txt``, ``rc.local``, installer scripts, or ARM32
binaries onto this card. Do not run the old autostart alongside the new
service. Re-enable neither launcher until its intended patch is configured.

Confirm the model and platform over SSH::

    cat /proc/device-tree/model
    cat /etc/os-release
    dpkg --print-architecture
    uname -r
    test -f /boot/firmware/overlays/proto-codec.dtbo

The playbook enforces Pi 3 Model B Plus, Debian 13 and ``aarch64``. Firmware
configuration is preserved except for the three owned, unparameterized
active directives: onboard audio, SPI, and the proto-codec overlay. These
are normalized into a final ``[all]`` block. It makes a backup before editing
and reboots automatically if boot settings change. Custom parameterized
forms of these directives must be reviewed before provisioning.

Build a release away from the appliance
--------------------------------------

Use a separate ARM64 Debian 13 build machine or VM. An x86 machine hosting
an ARM64 Debian VM is also suitable. Provisioning does not compile source
on the appliance. Cross-compilation with a sysroot is not implemented in
this first phase.

On the builder, install the compiler, headers and Pd package::

    sudo apt-get update
    sudo apt-get install build-essential binutils python3 git puredata-core puredata-dev
    git clone https://github.com/cdd3/terminal_tedium.git
    cd terminal_tedium
    git checkout implementation/trixie-arm64-appliance
    python3 deployment/scripts/build-release.py

Use a committed, clean checkout. Build outputs and local inventory files
are ignored by Git. The builder checks ARM64/Debian 13 and requires matching
``puredata-core`` and ``puredata-dev`` versions. Preserve the builder image
or its package snapshot to reproduce the compiler and Pd versions. The
release manifest records the source commit, compiler, Pd package version,
file checksums, architecture and OS major version. The build sets source
path mapping and normalized archive metadata; it does not claim identical
output across different compiler or system-header versions.

The result is ``dist/terminal_tedium-<commit>-arm64.tar.gz`` with a SHA256
sidecar. It includes four freshly built externals, ``libtt_gpio.so``, the
GPIO inspector, launcher and acceptance patch. Historical committed
``.pd_linux`` files are never packaged. Linux builds use installed Pd
headers rather than the old repository copy of ``m_pd.h``.

Copy the archive and its checksum file to the provisioning controller.
The controller may be ARM64 or x86. The release checker inspects the tar
without executing its binaries and rejects unexpected paths, symlinks,
missing files, checksum mismatches and non-AArch64 ELF files.

Provision from the controller
-----------------------------

Install the pinned Ansible tooling in a virtual environment::

    python3 -m venv .venv
    . .venv/bin/activate
    python3 -m pip install -r deployment/requirements.txt
    cp deployment/inventory.example.ini deployment/inventory.ini

Edit ``deployment/inventory.ini`` to set the unit's hostname or IP and SSH
administrator. Set an absolute local archive path and its SHA256 in a
local ``deployment/release-vars.yml`` file. Its two required variables are
``tt_release_archive`` and ``tt_release_sha256``. Optional
``tt_gpio_chip: auto`` selects exactly one accessible controller labelled
``pinctrl-bcm2835`` with 54 lines. An explicit ``/dev/gpiochipN`` is still
validated against that label; symlink aliases are deduplicated.

Run from the repository root::

    ansible-playbook -i deployment/inventory.ini deployment/provision.yml \
        -e @deployment/release-vars.yml --ask-become-pass

Omit ``--ask-become-pass`` if the administrator already has passwordless
sudo. Use normal SSH host-key verification. This is a real provisioning
run, including a possible reboot; Ansible check mode is not a supported
substitute for acceptance.

The playbook validates the artifact on the controller, installs the exact
Pd package version recorded by the builder, configures device permissions,
creates a dedicated ``tedium`` runtime account, and installs a release at
``/opt/terminal_tedium/releases/<archive-sha256>``. A ``current`` symlink
selects the active release. Runtime configuration lives in
``/etc/terminal_tedium/runtime.json`` and writable patch state belongs in
``/var/lib/terminal_tedium``. Release files stay root-owned.

A service start waits up to 30 seconds for the codec, GPIO and SPI devices,
restores named mixer controls, and then replaces the launcher process with
Pd. The named PCM ``hw:CARD=sndrpiproto,DEV=0`` is added with ``-alsaadd``
and selected with ``-audioadddev``. There is no dependency on the card's
numeric index. Pd runs headless with normal scheduling, stereo 48 kHz and
50 ms audio buffering. No login, GUI or network is required at runtime.
The service restarts on process failure, with a bounded retry rate.

Mixer settings are restored on every launch: Master 121 and Capture 23
(the historical 0 dB settings), Line In selected, line capture and digital
HiFi enabled, microphone capture, line bypass and mic sidetone disabled.
Other controls remain at their existing/default values.

Acceptance patch and cold-boot checks
------------------------------------

The acceptance patch enables DSP and passes left/right input to the
corresponding output at gain 0.25. It reads the ADC every 5 ms and prints
changed knob values at most once per second per channel. Switch and digital
input events are printed as they occur. The three outputs pulse high for
100 ms once per second. These are diagnostic pulses and logs.

Disconnect output jacks from anything that should not receive test pulses.
Use the LEDs first, then connect suitable measurement or trigger equipment.
Begin audio monitoring at a conservative level.

The tested mappings are:

* ``ADC_1`` through ``ADC_6``: six knobs/CV channels, legacy-scaled values 0..4001.
* ``EDGE_4``, ``EDGE_17``, ``EDGE_14``, ``EDGE_27``: four jack inputs.
* ``BUTTON_23``, ``BUTTON_24``, ``BUTTON_25``: 1 pressed, 0 released.
* ``HOLD_23``, ``HOLD_24``, ``HOLD_25``: nominal polling tick count on release.
* GPIO 16: output A and its LED.
* GPIO 12: output B and its LED.
* GPIO 26: illuminated tactile switch LED.

After provisioning, perform a full shutdown and power cycle, then reconnect
by SSH. Verify without manually launching Pd::

    systemctl is-enabled terminal_tedium
    systemctl status terminal_tedium --no-pager
    journalctl -b -u terminal_tedium --no-pager
    aplay -l
    arecord -l
    amixer -c sndrpiproto sget 'Output Mixer HiFi'
    amixer -c sndrpiproto sget 'Line'

Require ``TT_START`` with the intended controller and PCM,
``TT_PATCH: acceptance_v1``, ``SPI_STATUS: 1``, and no object-load,
GPIO/SPI or ALSA errors. An active service or a printed patch marker alone
is not proof that the audio device opened successfully.

Check both audio channels independently, all six controls, all three
buttons, all four jack inputs, and both trigger outputs and LEDs. GPIO 26
must pulse as well. The previous jack-input test confirmed trigger
responses; it did not scope-verify edge polarity. If precise edge behavior
is needed, include an oscilloscope/logic-analyzer test.

Stop/restart the service and confirm recovery::

    sudo systemctl restart terminal_tedium
    journalctl -u terminal_tedium --since '1 minute ago' --no-pager

Repeat cold boot with provisioning networking disconnected. Finally,
rerun the same playbook and inspect its recap for unintended changes or
reboots. Firmware task idempotence is covered locally, but full target
idempotence remains an acceptance requirement.

Save image SHA256, release SHA256, manifest/source commit, model, kernel,
Pd version, service logs, test results and observation duration in an
acceptance record. Mark the deployment accepted only after these checks.
No audible defects during a short test are not a quantified xrun result.

Troubleshooting and rollback
----------------------------

Stop the service before running manual Pd tests::

    sudo systemctl stop terminal_tedium

Use ``grep`` if ``rg`` is absent. Inspect current-boot service logs first,
then kernel messages for WM8731 or ASoC registration errors. Static MCLK
and dummy regulator notices were seen on the working unit; registration
alone does not establish audio operation. Confirm mixer routing and group
access to GPIO/SPI before debugging patch behavior.

The launcher fails on missing or ambiguous devices and mixer-command
errors. Pd itself may continue after an external or audio failure, so logs
and functional acceptance checks remain necessary. Normal shutdown attempts
to drive GPIO outputs low; crash, power-loss and unloaded-line levels
require hardware verification and are not guaranteed by this code.

To roll back the application, stop the service, point ``current`` at a
retained, known-good release directory, and restart it::

    sudo systemctl stop terminal_tedium
    sudo ln -sfn /opt/terminal_tedium/releases/PREVIOUS_SHA256 /opt/terminal_tedium/current
    sudo systemctl start terminal_tedium

This rolls back application files only. If the earlier release needs another
Pd package version, reprovision its archive with the matching available
packages. Firmware and OS recovery use the saved configuration backup and
base image. Keeping the original working SD card is the simplest physical
fallback during this phase.

Developer checks
----------------

On a Linux development machine with Pd headers installed::

    make -C software/externals all check
    python3 -m unittest discover -s deployment/tests -v
    ansible-playbook --syntax-check -i deployment/inventory.example.ini deployment/provision.yml
    cp deployment/templates/terminal_tedium.service.j2 /tmp/terminal_tedium.service
    systemd-analyze verify /tmp/terminal_tedium.service

The tests cover GPIO ownership, direction conflicts, pullups, initial/last
output state, release archive rejection, GPIO alias/identity handling and
actual Ansible firmware edits on a temporary file, including a second run
with zero changes. Firmware tests require Ansible on PATH. They do not
modify the development host's boot configuration.

References
----------

* Pd 0.55-2 named device argument handling:
  https://github.com/pure-data/pure-data/blob/0.55-2/src/s_main.c
* Pd 0.55-2 ALSA named PCM handling:
  https://github.com/pure-data/pure-data/blob/0.55-2/src/s_audio_alsa.c
* Raspberry Pi overlay documentation:
  https://github.com/raspberrypi/linux/blob/rpi-6.18.y/arch/arm/boot/dts/overlays/README

Later phases
------------

After fresh-card acceptance, user patch storage can be configured on the
OS card or faster USB storage as the patch's I/O needs dictate. Add mount
readiness, user-writable recording locations, patch dependencies and the
startup selector only when taking on those separate requirements. Other
Pi models, ARM32 and alternative engines also remain outside this phase.
