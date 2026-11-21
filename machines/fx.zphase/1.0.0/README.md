# ZPHASE 1.0.0

Airwindows' ZNotch2 swept by an LFO, as a send effect (Plugin API 3): a deep, vowel-like notch that moves up and down, free or in time with the Rytm, with 1 to 4 notches stacked at one centre and a stereo spread.

- Id: `fx.zphase`, kind: effect (a send effect on the Rytm's UFX slots)
- Boards: Pi 4 and Pi 5 (the same RMPA package; one file per board here)
- Plugin API: 3
- Licence: MIT
- Source: https://github.com/trigcondition/sidecar-firmware (`plugins/ufx_zphase`)

## Knobs

- Rate (RATE): 0 to 63 is free, 0.02 to 8 Hz; 64 to 127 is one sweep per note value at the Rytm's tempo (8BAR, 4BAR, 2BAR, 1BAR, 1/2, 1/4, 1/8, 1/16), locked to the song position while the Rytm plays
- Depth (DPTH): how far the sweep goes either side of the centre; 0 holds the notch still, 127 sweeps 2.5 octaves each way
- Centre (CNTR): the notch's centre frequency, 48 Hz at 0, about 650 Hz at 64, 4.75 kHz at 127
- Poles/Sprd (POLE): shown as a number. 0 to 31 is one notch, 32 to 63 two, 64 to 95 three, 96 to 127 four; more notches make a deeper, wider band-stop. Inside each range the value also sets the stereo spread: the right side's sweep runs ahead of the left's by up to half a cycle (the first value of a range is mono)

The return is wet only: the send level is the mix. With the track's own dry sound also on the main mix the notch is shallower.

At the fixed input level the stage clips of the original rarely engage, so this is a clean swept notch with the original's high-pass and low-pass rounding, not a saturating one.

## Credits and licence

The algorithm is ZNotch2 by Chris Johnson (Airwindows, MIT, https://github.com/airwindows/airwindows, plugins/LinuxVST/src/ZNotch2, read at commit 143a86df3642881e0be4bf827815050721063b41), ported to C. The port and glue are MIT, Copyright 2026 trigcondition and contributors.

This is a Sidecar project package listed in the community registry; the registry's trust notes in CONTRIBUTING.md apply: a machine is native code with no sandbox.
