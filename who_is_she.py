#!/usr/bin/python3.6

from PIL import Image
import numpy as np

def poke_png_to_sillhouette(image_path):
    ''' Flattens all non transparent pixels to the classic "who's that pokemon" blue.

        Code modified from this thread: https://stackoverflow.com/a/3753428
    '''
    im = Image.open(image_path)
    im = im.convert('RGBA')

    data = np.array(im)
    _, _, _, alpha = data.T

    non_transparent_areas = (alpha != 1)
    data[..., :-1][non_transparent_areas.T] = (13, 93, 164)

    im2 = Image.fromarray(data)
    im2.show()


poke_png_to_sillhouette('img.png')
