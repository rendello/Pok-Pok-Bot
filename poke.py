#!/usr/bin/python3.6

from fuzzywuzzy import fuzz
import asyncio
import discord
from discord.ext import commands

from main import get_pokemon_and_image
from Core.secret_token import client_secret



# ------ User functions --------
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



# ---------- Classes -----------
class Match():
    def __init__(self, ctx, *, pokemon_name):
        self.server = ctx.guild
        self.channel = ctx.channel
        self.pokemon_name = pokemon_name
        self.original_image_path = str()
        self.timeout_flag = asyncio.Event()

    async def timer(self, seconds):
        await asyncio.sleep(seconds)
        self.timeout_flag.set()



def pokemon_in_text(*, text, pokemon_name):
    pokemon_name = pokemon_name.lower()

    if len(text) > 100:
        return False

    if fuzz.token_set_ratio(text, pokemon_name) > 90:
        return True
    return False



# ---------- Globals -----------
bot = commands.Bot(command_prefix="!")
matches = {}



# ---------- Commands ----------
@bot.command()
async def poke(ctx):
    pokemon, image_path, original_image_path = get_pokemon_and_image()
    await ctx.channel.send(file=discord.File(image_path))

    match_key = ctx.message.channel.id

    print(pokemon['name'])
    matches[match_key] = Match(ctx, pokemon_name=pokemon['name'])

    matches[match_key].original_image_path = original_image_path


@bot.command()
async def d(ctx):
    print(matches)



# ----------- Events -----------
@bot.event
async def on_message(message):
    if (message.channel.id in matches.keys()) and (message.author.id != bot.user.id):
        clean_message = clean_input_string(message.content)
        match = matches[message.channel.id]

        if pokemon_in_text(text=clean_message, pokemon_name=match.pokemon_name):
            await message.channel.send(file=discord.File(match.original_image_path))
            await message.channel.send(f"That's right, {message.author.mention}! It's {match.pokemon_name}!")

    # Stops on_message from blocking all other commands.
    await bot.process_commands(message)



bot.run(client_secret)
