#!/usr/bin/python3.6

from PIL import Image, ImageEnhance
import numpy as np


def poke_png_to_sillhouette(image_path, color_tuple):
    ''' Flattens all non transparent pixels into an RGB color.

    Code modified from this thread: https://stackoverflow.com/a/3753428

    Args:
        image_path (string): The path of the image to be flattened.
        color_tuple (tuple): The RGB components from 0-255.

    Returns:
        PIL.Image: A flattened silhouette of the image.
    '''

    im = Image.open(image_path)
    im = im.convert('RGBA')

    data = np.array(im)
    _, _, _, alpha = data.T

    non_transparent_areas = (alpha != 1)
    data[..., :-1][non_transparent_areas.T] = color_tuple

    im2 = Image.fromarray(data)

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


def opacity_friendly_paste(base_image, opacity_image, x, y):
    ''' Pastes while preserving opacity information.

    Normal paste cannot merge two images with opacity together. This function
    abstracts the steps needed to allow that to happen. Returns a new image
    instead of editing in place as normal Image.paste() does.

    Args:
        base_image (PIL.Image): The image to be pasted onto.
        opacity_image (PIL.Image): The image to be pasted on top.
        x (int): The x location of the pasting.
        y (int): The y location of the pasting.

    Returns:
        PIL.Image: A composite of the two images.
    '''

    base_width, base_height = base_image.size

    new_image = Image.new('RGBA', (base_width, base_height))
    new_image.paste(opacity_image, (x, y), opacity_image)
    
    return Image.alpha_composite(base_image, new_image)


def create_figure(poke_image):
    ''' Creates a pokemon's silhouette from its original image.

    Args:
        poke_image (PIL.Image): A picture of a pokemon with a transparent background.

    Returns:
        figure (PIL.Image): A full shrouded image of the pokemon, combining
            multiple silhouettes.
    '''

    figure = poke_png_to_sillhouette(poke_image, (0, 0, 0))
    figure = reduce_opacity(figure, 0.5)

    im1 = poke_png_to_sillhouette(poke_image, (7, 61, 93))
    im2 = poke_png_to_sillhouette(poke_image, (13, 93, 164))

    figure.paste(im1, (10, 0), im1)
    figure.paste(im2, (23, 2), im2)
    return figure


def resize(img, new_width):
    ''' Scales an image according to width.
    
    Modified from: https://opensource.com/life/15/2/resize-images-python.
    '''
    wpercent = (new_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((new_width, hsize), Image.ANTIALIAS)
    return img


def put_figure_on_template(figure):
    figure = resize(figure, 200)
    bg = Image.open('template.png')
    bg = opacity_friendly_paste(bg, figure, 30, 30)
    return bg


def create_wtp_images(image_path):
    original_figure = Image.open(image_path)
    original_image = put_figure_on_template(original_figure)

    figure = create_figure(image_path)
    full_image = put_figure_on_template(figure)

    return (full_image, original_image)

