Implementation validation record
================================

Date: 2026-10-07

Local development checks
------------------------

* All four externals, shared GPIO backend and inspector compiled on the
  development host against Pd 0.55 headers, with the configured warnings
  enabled. This was an x86 development build, not the deployable ARM64 build.
* Mocked GPIO ownership/ioctl tests passed.
* Seven deployment tests passed, including archive corruption, wrong ELF
  architecture, unsafe member rejection, controller identity/alias handling,
  and the actual firmware-edit tasks run twice through Ansible on a fixture.
  The second firmware run reported zero changes.
* Ansible 2.19.3 playbook syntax check passed.
* systemd-analyze accepted the service unit.
* Shared library inspection confirmed ``libtt_gpio.so`` dependency and
  ``$ORIGIN`` runtime search path.
* Acceptance patch object/connection indices were checked structurally.
  The patch has not been loaded into Pd on this development host.

Previously reported target evidence
----------------------------------

The user compiled the earlier prototype on ARM64 with Pd 0.55.2 and reported
working stereo input/output, six ADC channels, three buttons, four trigger
inputs, GPIO 16/12 output A/B jacks and LEDs, and GPIO 26 switch LED. Audio
alongside control polling had no obvious audible defects during the reported
trial. Trigger edge polarity was not measured with an oscilloscope.

The new implementation also changes header selection, stops ADC reads after
a failed SPI transfer, and adds the deployment scripts and acceptance patch.
Those changes are not certified by the earlier prototype test.

Pending release acceptance
--------------------------

* Build the release on the separate ARM64 Debian 13 builder.
* Establish and retain the exact fresh base image and builder package inputs.
* Provision a spare card and verify full playbook idempotence.
* Exercise the bundled acceptance patch on the real unit.
* Verify cold boot without provisioning networking and service recovery.

No fresh-card deployment, full ARM64 release build, target service test or
quantified latency/xrun measurement was performed in this development session.
