#!/usr/bin/python3.6

import random

import urllib.request 
from PIL import Image
from pathlib import Path
from tempfile import NamedTemporaryFile

from Core.db_context_manager import dbopen

from Core.create_image import create_wtp_images


cachedir = './Cache'

def get_random_pokemon():
    '''
    Args:
        None

    Returns:
        pokemon: a <dict> with 'pokemon' (the creature's name <str>) and 'id' (its id <str>).
    '''
    with dbopen('Core/pokemon.db') as c:

        # Must use rowid, as id is technically text.
        c.execute('SELECT MAX(rowid) FROM pokemon;')
        highest_id = c.fetchone()[0]

        pokemon_id = random.randint(1, highest_id)
        c.execute('SELECT pokemon, id FROM pokemon WHERE id=?;', [str(pokemon_id)])
        result = c.fetchone()

        pokemon = {'name': result[0], 'id': result[1]}

        return pokemon


def fetch_image(pokemon_id):
    def pad(pokemon_id):
        if len(pokemon_id) < 3:
            pokemon_id = '0' + pokemon_id
            pokemon_id = pad(pokemon_id)
        return pokemon_id

    pokemon_id = pad(pokemon_id)

    url = f'https://assets.pokemon.com/assets/cms2/img/pokedex/full/{pokemon_id}.png'

    # The first value is the path to the image's tempfile.
    image_path = urllib.request.urlretrieve(url)[0]
    
    return image_path


def cached_version_exists(pokemon, shrouded_path, unshrouded_path):
    if Path(shrouded_path).is_file() and Path(unshrouded_path).is_file():
        return True


def save_to_tempfile(image):
    tempfile = NamedTemporaryFile(suffix='.png', delete=False)
    image.save(tempfile.name, 'PNG')

    return tempfile.name


def get_pokemon_and_image():
    ''' Gets pokemon name, id, and WTP images (shrouded and not)

    Returns:
        tuple:
            The first value is a dict that contains 'name' (a string containing
            the pokemon's name), and id, a three-number string representing the
            pokemon's ID. Eg:

                {'name': 'Pikachu', 'id': '025'}

            The second value is the path to the cached shrouded WTP image.
            The third is the path to the unshrouded variant.
    '''
    pokemon = get_random_pokemon()
    #pokemon = {'name': 'Pikachu', 'id': '025'}

    shrouded_path = f'{cachedir}/{pokemon["name"]}_shrouded.png'
    unshrouded_path = f'{cachedir}/{pokemon["name"]}_unshrouded.png'

    if cached_version_exists(pokemon, shrouded_path, unshrouded_path):
        shrouded_image = Image.open(shrouded_path)
        unshrouded_image = Image.open(unshrouded_path)
    else:
        # Create images from pokedex
        image_path = fetch_image(pokemon['id'])
        shrouded_image, unshrouded_image = create_wtp_images(image_path)

        # Saved cached versions
        shrouded_image.save(shrouded_path, 'PNG')
        unshrouded_image.save(unshrouded_path, 'PNG')

    return (pokemon, shrouded_path, unshrouded_path)
