#!/usr/bin/python3.6

from fuzzywuzzy import fuzz
import asyncio
import discord
from discord.ext import commands

from main import get_pokemon_and_image
from Core.secret_token import client_secret



# ------ User functions --------
def clean_input_string(input_string):
    ''' Replaces unwanted characters with spaces.
    
    Args:
        input_string (str): A string to be cleaned.

    Returns:
        str: A string containing only the accepted characters.
    '''
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
        self.timeout_flag = 'active'


    async def set_timer(self, seconds):
        await asyncio.sleep(seconds)
        await self.end('failure')


    async def end(self, nature):
        ''' Ends a match.

        Args:
            nature (str): 'success' if match won in time, 'failure' if not.
        '''
        if nature == 'failure':
            print('match lost')
        else:
            print('match won')




def pokemon_in_text(*, text, pokemon_name):
    ''' Finds the given pokemon_name in the given text.
    
    Technically  pokemon_name can be any string. Spelling doesn't need to perfect, as the
    function uses fuzzy searching.

    Args:
        text (str): The string in which pokemon_name is searched for in.
        pokemon_name (str): The string to be fuzzy-searched for in the text.

    Returns:
        bool: True if found (fuzzily), False if not
    '''
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

    match = matches[match_key]

    match.original_image_path = original_image_path
    await match.set_timer(5)


@bot.command()
async def d(ctx):
    print(matches)



# ----------- Events -----------
@bot.event
async def on_message(message):
    ''' Checks for pokemon in messages after matches have been called.

    Args:
        message (discord.message.Message): automatically passed for every message of
        every connected server.
    '''

    # Only look for pokemon in channels with matches
    if (message.channel.id in matches.keys()) and (message.author.id != bot.user.id):
        match = matches[message.channel.id]

        clean_message = clean_input_string(message.content)

        if pokemon_in_text(text=clean_message, pokemon_name=match.pokemon_name):
            await message.channel.send(file=discord.File(match.original_image_path))
            await message.channel.send(f"That's right, {message.author.mention}! It's {match.pokemon_name}!")
            await match.end('success')

    # Stops on_message from blocking all other commands.
    await bot.process_commands(message)



bot.run(client_secret)
