import numpy as np
from skimage import transform
import tifffile as tfl
import time
import os
import tisgrabber as ic


def setCameraParams(cam, params):
    """ Set parameters of TIS camera object. Their code sucks.

    :param cam: (TIC_CAM) instantiated camera object
    :param params: (dict) dictionary of camera parameters to set
    :return: nothing. camera parameters edited in place.
    """
    # honestly ugh

    cam.SetPropertyValue('Brightness', 'Value', params['brightness'])
    cam.SetPropertyValue('Contrast', 'Value', params['contrast'])

    if params['gain'] == 'auto':
        cam.SetPropertySwitch('Gain', 'Auto', 1)
    else:
        cam.SetPropertyValue('Gain', 'Value', params['gain'])

    # no auto - hard coded to avoid strobe probs
    cam.SetPropertyValue('Exposure', 'Auto', 0)

    cam.SetPropertyAbsoluteValue('Exposure', 'Value', params['exposure'])
    cam.SetPropertyValue('Exposure', 'Auto reference', params['exposureAutoRef'])

    if params['exposureAutoMax'] == 'auto':
        cam.SetPropertySwitch('Exposure', 'Auto max value auto', 1)
    else:
        raise ValueError('only \'auto\' works right now.')

    if params['highlightReduction']:
        cam.SetPropertySwitch('Highlight reduction', 'Value', 1)
    else:
        cam.SetPropertySwitch('Highlight reduction', 'Value', 0)

    cam.SetPropertyValue('Sharpness', 'Value', params['sharpness'])
    cam.SetPropertyValue('Gamma', 'Value', params['gamma'])
    cam.SetPropertyValue('Denoise', 'Value', params['denoise'])

    if params['autoCenter']:
        cam.SetPropertySwitch('Partial scan', 'Partial scan auto center', 1)
    else:
        cam.SetPropertySwitch('Partial scan', 'Partial scan auto center', 0)
        cam.SetPropertyValue('Partial scan', 'X offset', params['xOffset'])
        cam.SetPropertyValue('Partial scan', 'Y offset', params['yOffset'])

    if params['trigger']:
        cam.SetPropertySwitch('Trigger', 'Enable', 1)
    else:
        cam.SetPropertySwitch('Trigger', 'Enable', 0)

    if params['strobe']:
        cam.SetPropertySwitch('Strobe', 'Enable', 1)
    else:
        cam.SetPropertySwitch('Strobe', 'Enable', 0)

    if params['strobePolarity']:
        cam.SetPropertySwitch('Strobe', 'Polarity', 1)
    else:
        cam.SetPropertySwitch('Strobe', 'Polarity', 0)

    if params['toneMapping']:
        cam.SetPropertySwitch('Tone mapping', 'Enable', 1)
    else:
        cam.SetPropertySwitch('Tone mapping', 'Enable', 0)


def acquireStack(cam, acqLengthS, doStrobe, downscaleTuple, animal, outdir, saveTxt):
    """ Take a timed image stack with the camera.

    :param cam: (TIC_CAM) instantiated camera object
    :param acqLengthS: (int) desired acquisition length in seconds
    :param doStrobe: (bool) whether or not to send strobe signal, default True
    :param downscaleTuple: (tuple) downscaling factors in (T, x, y), e.g. (1, 2, 2) for 2x downscale
    :param animal: (str) animal ID
    :param outdir: (str) folder to save stack to
    :param saveTxt: (bool) whether or not to save params as a txt file
    :return stack: (np array) acquired image stack
    """
    stack = []
    t_start = time.time()
    t_end = t_start + acqLengthS

    cam.StartLive(1)

    if doStrobe:
        cam.SetPropertyValue('GPIO', 'GP Out', 1)
        cam.SetPropertyValue('GPIO', 'Write', 1)

    while time.time() < t_end:
        cam.SnapImage()
        im = cam.GetImage()  # appears to have three identical(?) frames
        stack.append(np.mean(im, axis=2))  # averaging to one frame

    if doStrobe:
        cam.SetPropertyValue('GPIO', 'GP Out', 0)
        cam.SetPropertyValue('GPIO', 'Write', 1)
    cam.StopLive()

    stack = np.r_[stack]
    stack = transform.downscale_local_mean(stack, downscaleTuple)
    stack = stack.astype('int16')

    timeStr = time.strftime("_%y%m%d_%H-%M-%S", time.localtime(t_start))
    outfile = os.path.join(outdir, '{}{}.tif'.format(animal, timeStr))
    tfl.imsave(outfile, stack)
    nFrames = stack.shape[0]
    
    print('Saved {} frames to {}'.format(nFrames, outfile))

    if saveTxt:
        params = getCameraParams(cam)
        f = open(os.path.join(outdir,'{}{}.txt'.format(animal, timeStr)))
        f.write(str(params))
        f.close()

    return stack

def getCameraParams(cam):
    """ Create a dict of imaging params.

    :param cam: camera object to collect params from
    :return: (dict) of parameters
    """
    # automatic ones here
    if cam.GetPropertySwitch('Gain', 'Auto') == 1:
        gain = 'auto'
    else:
        gain = cam.GetPropertyValue('Gain', 'Value')

    if cam.GetPropertySwitch('Exposure', 'Auto max value auto') == 1:
        automax = 'auto'
    else:
        automax = cam.GetPropertyValue('Exposure', 'Auto max value')

    if cam.GetPropertySwitch('Highlight reduction', 'Value') == 1:
        highlightReduction = True
    else:
        highlightReduction = False

    if cam.GetPropertySwitch('Partial scan', 'Partial scan auto center') == 1:
        autoCenter = True
    else:
        autoCenter = False

    if cam.GetPropertySwitch('Trigger', 'Enable') == 1:
        trigger = True
    else:
        trigger = False

    if cam.GetPropertySwitch('Strobe', 'Enable') == 1:
        strobe = True
    else:
        strobe = False

    if cam.GetPropertySwitch('Strobe', 'Polarity') == 1:
        polarity = True
    else:
        polarity = False

    if cam.GetPropertySwitch('Tone mapping', 'Enable') == 1:
        toneMapping = True
    else:
        toneMapping = False

    params = {
        'brightness': cam.GetPropertyValue('Brightness', 'Value'),
        'contrast': cam.GetPropertyValue('Gain', 'Value'),
        'gain': gain,
        'exposure': cam.GetPropertyAbsoluteValue('Exposure', 'Value'),
        'exposure auto ref': cam.GetPropertyValue('Exposure', 'Auto reference'),
        'exposure auto max': automax
        'highlight reduction': highlightReduction,
        'sharpness': cam.GetPropertyValue('Sharpness', 'Value'),
        'gamma': cam.GetPropertyValue('Gamma', 'Value'),
        'denoise': cam.GetPropertyValue('Denoise', 'Value'),
        'auto center': autoCenter,
        'x offset': cam.GetPropertyValue('Partial scan', 'X offset'),
        'y offset': cam.GetPropertyValue('Partial scan', 'Y offset'),
        'trigger': trigger,
        'strobe': strobe,
        'strobe polarity': polarity,
        'tone mapping': toneMapping
             }
    return params
