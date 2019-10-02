import numpy as np
from skimage import transform
import tifffile as tfl
import time
import os
import u6


def _set_and_check(camFn, *pv):
    """ Check that camera parameters are being set correctly.
    The tisgrabber C wrapper returns a value on setting.
    See their tisgrabber.h file for details on retvals.

    Args:
        camFn: (fn) TIS_CAM function
        *pv: args for function

    Returns:
        passes if param is set correctly.
        raises RuntimeError if param is not set correctly.
    """
    retval = camFn(*pv)
    if retval != 1:
        raise RuntimeError('Error calling into API: %s, retval %d' % (str(camFn), retval))


def setCameraDefaults(cam):
    """

    Args:
        cam: (TIS_CAM) camera object

    Returns:
        nothing.

    """
    _set_and_check(cam.open, 'DMK 72BUC02 7610448')
    _set_and_check(cam.SetVideoFormat, 'Y800 (640x480)')
    _set_and_check(cam.SetFrameRate, 15.0)

    print('Camera properties set successfully.')


def setCameraParams(cam, params):
    """ Set imaging parameters.

    Args:
        cam: (TIC_CAM) instantiated camera object
        params: (dict) camera parameters

    Returns:
        nothing.

    """
    # honestly ugh

    _set_and_check(cam.SetPropertyValue, 'Brightness', 'Value', params['brightness'])
    _set_and_check(cam.SetPropertyValue, 'Contrast', 'Value', params['contrast'])

    if params['gain'] == 'auto':
        _set_and_check(cam.SetPropertySwitch, 'Gain', 'Auto', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Gain', 'Auto', 0)
        _set_and_check(cam.SetPropertyValue, 'Gain', 'Value', params['gain'])

    if params['exposure'] == 'auto':
        _set_and_check(cam.SetPropertySwitch, 'Exposure', 'Auto', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Exposure', 'Auto', 0)
        _set_and_check(cam.SetPropertyAbsoluteValue, 'Exposure', 'Value', params['exposure'])

    _set_and_check(cam.SetPropertyValue, 'Exposure', 'Auto Reference', params['exposureAutoRef'])

    if params['exposureAutoMax'] == 'auto':
        raise ValueError('Trouble setting auto right now. Use a float value.')
        # hypothesis: both auto exposure and exposure auto max auto are ID'd "Auto", which causes problems.
        # _set_and_check(cam.SetPropertySwitch, 'Auto Max Value Auto', 'Enable', 1)
    else:
        _set_and_check(cam.SetPropertyAbsoluteValue, 'Exposure', 'Auto Max Value', params['exposureAutoMax'])

    if params['highlightReduction']:
        _set_and_check(cam.SetPropertySwitch, 'Highlight reduction', 'Enable', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Highlight reduction', 'Enable', 0)

    _set_and_check(cam.SetPropertyValue, 'Sharpness', 'Value', params['sharpness'])
    _set_and_check(cam.SetPropertyValue, 'Sharpness', 'Value', params['sharpness'])
    _set_and_check(cam.SetPropertyValue, 'Gamma', 'Value', params['gamma'])
    _set_and_check(cam.SetPropertyValue, 'Denoise', 'Value', params['denoise'])

    if params['autoCenter']:
        _set_and_check(cam.SetPropertySwitch, 'Partial scan', 'Auto-center', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Partial scan', 'Auto-center', 0)
        _set_and_check(cam.SetPropertyValue, 'Partial scan', 'X Offset', params['xOffset'])
        _set_and_check(cam.SetPropertyValue, 'Partial scan', 'Y Offset', params['yOffset'])

    if params['trigger']:
        _set_and_check(cam.SetPropertySwitch, 'Trigger', 'Enable', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Trigger', 'Enable', 0)

    if params['strobe']:
        _set_and_check(cam.SetPropertySwitch, 'Strobe', 'Enable', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Strobe', 'Enable', 0)

    if params['strobePolarity']:
        _set_and_check(cam.SetPropertySwitch, 'Strobe', 'Polarity', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Strobe', 'Polarity', 0)

    if params['toneMapping']:
        _set_and_check(cam.SetPropertySwitch, 'Tone Mapping', 'Enable', 1)
    else:
        _set_and_check(cam.SetPropertySwitch, 'Tone Mapping', 'Enable', 0)

    print('Parameters set successfully.')


def acquireStack(cam, nFrames, downscaleTuple, animal, outdir):
    """   Get an image stack from the camera.
     Args:
        cam: (TIS_CAM) initialized camera object
        nFrames: (int) number of frames to acquire
        sendCounter (bool) whether or not to send strobe signal
        downscaleTuple: (tuple) downscale factor in (z, x, y), e.g. (1, 2, 2) for 2x downscale
        animal: (str) animal ID, used for output naming
        outdir: (str) path to output directory

    Returns:
        stack: (np.ndarray) image stack in (z, x, y)
    """
    # setup the labjack
    dioPortNum = 0  # FIO0
    u6Obj = u6.U6()
    u6Obj.configU6()
    u6Obj.configIO()
    u6Obj.setDOState(dioPortNum, state=0)

    stack = []

    cam.StartLive(1)
    # Not using 191001: strobe code below.
    # if sendCounter:
    #     _set_and_check(cam.SetPropertyValue, 'GPIO', 'GP Out', 1)
    #     _set_and_check(cam.PropertyOnePush, 'GPIO', 'Write')
    t_start = time.time()
    for iF in np.arange(nFrames):
        pulseLengthTicks = int(1000/64)
        u6Obj.getFeedback(u6.BitDirWrite(dioPortNum, 1),
                          u6.BitStateWrite(dioPortNum, State=1),
                          u6.WaitShort(pulseLengthTicks),
                          u6.BitStateWrite(dioPortNum, State=0))
        cam.SnapImage()
        im = cam.GetImage()  # appears to have three identical(?) frames
        im = np.mean(im, axis=2).astype('int16')
        stack.append(im)  # averaging to one frame

    # Not using 191001: strobe code below.
    # if sendCounter:
    #     _set_and_check(cam.SetPropertyValue, 'GPIO', 'GP Out', 0)
    #     _set_and_check(cam.PropertyOnePush, 'GPIO', 'Write')

    cam.StopLive()

    print('Done. Downsizing and saving.')
    stack = np.r_[stack]
    stack = transform.downscale_local_mean(stack, downscaleTuple)
    stack = stack.astype('int16')

    timeStr = time.strftime("_%y%m%d_%H-%M-%S", time.localtime(t_start))
    outfile = os.path.join(outdir, '{}{}.tif'.format(animal, timeStr))
    tfl.imsave(outfile, stack)
    nFrames = stack.shape[0]

    print('Saved {} frames to {}'.format(nFrames, outfile))

    return stack
