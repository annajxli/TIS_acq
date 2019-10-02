---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.2.4
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

## Notebook for camera control
- AL 190928: For pupil tracking i/o. Uses (poorly documented) code from TIS on DMK 72BUC02.


----
#### Start the camera and set video format, framerate.

setCameraDefaults sets our defaults:
- DMK 72BUC02 7610448
- 7800 (640x480)
- 15.0 fps

To use a different camera or settings, open the device selection dialog.

Note that the camera parameters for a different model may be different, so setting them may throw errors.

```python
import os, sys
import tisgrabber as ic
import ICtools

# init camera object
cam = ic.TIS_CAM()

ICtools.setCameraDefaults(cam)

# or do this: open device selection GUI
# cam.ShowDeviceSelectionDialog()
```

----
#### Set video properties

Figure out the params in IC Capture first, then enter them here.

```python
params = {
    'brightness': 0, # default 0
    'contrast': 0, # default 0
    'gain': 7, # int or 'auto', case sensitive
    'exposure': 1/15, # same as framerate
    'exposureAutoRef': 128, # default 128
    'exposureAutoMax': 1/15, # no 'auto' here
    'highlightReduction': False, # bool
    'sharpness': 0, # default 0
    'gamma': 100, # default 100
    'denoise': 0, # default 0
    'autoCenter': False, # bool, keep false if setting manually
    'xOffset': 1168, # adjust to IC Capture
    'yOffset': 0, # adjust to IC Capture
    'trigger': False, # bool, we don't have one
    'strobe': False, # bool, default True
    'strobePolarity': False, # bool, default False
    'toneMapping': False # bool
         }

ICtools.setCameraParams(cam, params)
```

----
#### Acquisition here

Notes:
- Using Labjack to send TTL pulses now (no strobe)

```python
# the preceding r is needed for windows
animal = 'i2224-post-behav'
outdir = r'C:\Users\histedlabuser\Videos\pupilTracking\191001-i2224'

stack = ICtools.acquireStack(cam, nFrames=1800, downscaleTuple=(1,2,2), 
                             animal=animal, outdir=outdir)
```

#### Start/stop the live feed
If you want to look at the feed without acquiring. Returns 1 on success.

```python
# window stops responding if you click on it?
cam.StartLive(1) # 1 makes a window pop up, showing you the image
```

```python
cam.StopLive()
```

:)
