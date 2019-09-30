---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.1'
      jupytext_version: 1.2.3
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

## Notebook for camera control
- AL 190928: For pupil tracking i/o. Uses (poorly documented) code from TIS on DMK 72BUC02.


----
#### This cell opens a device selection dialog

Set these things:

- device name
- video format (incl. binning)
- framerate

Hit "Ok"

```python
import os, sys
import tisgrabber as ic
import ICtools

# init camera object
cam = ic.TIS_CAM()

# set the settings we usually use: prints 1 on success
cam.open('DMK 72BUC02 7610448')
cam.SetVideoFormat('Y800 (640x480 VGA)')
cam.SetFrameRate(15.0)

# or do this: open device selection GUI
# cam.ShowDeviceSelectionDialog()
```

----
#### Set video properties

For items like gain/exposure, it may be prudent to figure out the values in IC Capture first, then enter them here.

```python
params = {
    'brightness': 0, # default 0
    'contrast': 0, # default 0
    'gain': 'auto', # int or 'auto', case sensitive
    'exposure': 1/14, # greater than frame time: usually 1/15s
    'exposureAutoRef': 128, # default 128
    'exposureAutoMax': 'auto', # having trouble setting this value. use default 'auto'
    'highlightReduction': False, # bool
    'sharpness': 0, # default 0
    'gamma': 100, # default 100
    'denoise': 0, # default 0
    'autoCenter': False, # bool, keep false if setting manually
    'xOffset': 0, # adjust to IC Capture
    'yOffset': 0, # adjust to IC Capture
    'trigger': False, # bool, we don't have one
    'strobe': True, # bool, default True
    'strobePolarity': False, # bool, default False
    'toneMapping': False # bool
         }

ICtools.setCameraParams(cam, params)
```

----
#### Acquisition here
- NEEDS TESTING: strobe matches up w/ frame count.

Notes:
- Each snapped image is three frames, so averaging those down.
- Images are default float64. I'm changing to int16 for size purposes.
    - This way, 1 second of 15 fps 640x480 is about 8 mb.

```python
# the preceding r is needed for windows
animal = 'i2227'
outdir = r'C:\Users\anna\Videos\pupilTracking'

stack = ICtools.acquireStack(cam, acqLengthS=10, doStrobe=True,
                             downscaleTuple=(1,1,1), animal=animal,
                             outdir=outdir)
```

#### Start/stop the live feed
If you want to look at the feed without acquiring.

```python
# window stops responding if you click on it?
cam.StartLive(1) # 1 makes a window pop up, showing you the image
```

```python
cam.StopLive()
```

:)
