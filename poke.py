#!/usr/bin/python3.6

from fuzzywuzzy import fuzz

from Core.secret_token import client_secret

import discord
from discord.ext import commands

from main import get_pokemon_and_image


class Match():
    def __init__(*, server, channel, pokemon):
        self.server = channel
        self.channel = channel
        self.pokemon = pokemon


def clean_input_string(input_string):
    input_string = input_string.lower()
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    clean_string = str()

    for char in input_string:
        if char not in alphabet:
            clean_string += ' '
        else:
            clean_string += char
    return clean_string


def pokemon_in_text(*, text, pokemon):
    pokemon = pokemon.lower()
    words = text.split()

    if len(words) > 50:
        return False

    for word in words:
        if fuzz.ratio(word, pokemon) > 90:
            return True
    return False

    

bot = commands.Bot(command_prefix="!")


@bot.command()
async def poke(ctx):
    pokemon, image_path = get_pokemon_and_image()
    await ctx.channel.send(file=discord.File(image_path))

text = clean_input_string("HAY GUYZZ!!! I loveee the PicaKHCHU PILCACHU pokeemon!!!! Cahr Charizo Burger Yommmmmm")
print(pokemon_in_text(text=text, pokemon='Charizard'))

bot.run(client_secret)
