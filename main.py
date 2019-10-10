#!/usr/bin/python3.6

import random

import urllib.request 
from PIL import Image
from tempfile import NamedTemporaryFile

from Core.db_context_manager import dbopen

from Core.create_image import create_full_image


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

        pokemon = {'pokemon': result[0], 'id': result[1]}

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


def get_pokemon_and_image():
    pokemon = get_random_pokemon()
    image_path = fetch_image(pokemon['id'])
    im = create_full_image(image_path)
    tempfile = NamedTemporaryFile(suffix='.png', delete=False)

    im.save(tempfile.name, 'PNG')

    return (pokemon, tempfile.name)
