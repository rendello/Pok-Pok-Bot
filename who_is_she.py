#!/usr/bin/python3.6

from PIL import Image, ImageEnhance
import numpy as np


def poke_png_to_sillhouette(image_path, color_tuple):
    ''' Flattens all non transparent pixels.

        Code modified from this thread: https://stackoverflow.com/a/3753428
    '''
    im = Image.open(image_path)
    im = im.convert('RGBA')

    data = np.array(im)
    _, _, _, alpha = data.T

    non_transparent_areas = (alpha != 1)
    data[..., :-1][non_transparent_areas.T] = color_tuple

    im2 = Image.fromarray(data)
    #im2.show()

    return im2


def reduce_opacity(im, opacity):
    """ Returns an image with reduced opacity.

        Modified from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/362879
    """
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im


def create_figure(poke_image):
    shadow = poke_png_to_sillhouette(poke_image, (0, 0, 0))
    shadow = reduce_opacity(shadow, 0.5)

    im1 = poke_png_to_sillhouette(poke_image, (7, 61, 93))
    im2 = poke_png_to_sillhouette(poke_image, (13, 93, 164))

    shadow.paste(im1, (10, 0), im1)
    shadow.paste(im2, (23, 2), im2)
    return shadow


def resize(img, new_width):
    ''' Modified from: https://opensource.com/life/15/2/resize-images-python. '''
    wpercent = (new_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((new_width, hsize), Image.ANTIALIAS)
    return img


def put_figure_on_template(figure):
    figure = resize(figure, 200)
    bg = Image.open('small_template.png')
    bg.paste(figure, (30, 30), figure)
    bg.show()


figure = create_figure('img.png')
put_figure_on_template(figure)

