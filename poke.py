#!/usr/bin/python3.6

from fuzzywuzzy import fuzz

from Core.secret_token import client_secret

import discord
from discord.ext import commands

from main import get_pokemon_and_image


class Match():
    def __init__(self, ctx, *, pokemon_name):
        self.server = ctx.guild
        self.channel = ctx.channel
        self.pokemon_name = pokemon_name


def clean_input_string(input_string):
    input_string = input_string.lower()
    accepted_chars = 'abcdefghijklmnopqrstuvwxyz: '
    clean_string = str()

    for char in input_string:
        if char not in accepted_chars:
            clean_string += ' '
        else:
            clean_string += char
    return clean_string


def pokemon_in_text(*, text, pokemon_name):
    pokemon_name = pokemon_name.lower()

    if len(text) > 100:
        return False

    if fuzz.token_set_ratio(text, pokemon_name) > 90:
        return True
    return False

    

bot = commands.Bot(command_prefix="!")
matches = {}


@bot.command()
async def poke(ctx):
    pokemon, image_path = get_pokemon_and_image()
    await ctx.channel.send(file=discord.File(image_path))

    match_key = ctx.message.channel.id

    print(pokemon['name'])
    matches[match_key] = Match(ctx, pokemon_name=pokemon['name'])


@bot.command()
async def d(ctx):
    print(matches)


@bot.event
async def on_message(message):
    if message.channel.id in matches.keys():
        clean_message = clean_input_string(message.content)

        if pokemon_in_text(text=clean_message, pokemon_name=matches[message.channel.id].pokemon_name):
            await message.channel.send("NICE")


    # Stops on_message from blocking all other commands.
    await bot.process_commands(message)

bot.run(client_secret)
