#!/usr/bin/python3.6

from fuzzywuzzy import fuzz
import asyncio
import discord
from discord.ext import commands

import random

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
    accepted_chars = 'abcdefghijklmnopqrstuvwxyz: é'
    clean_string = str()

    for char in input_string:
        if char not in accepted_chars:
            clean_string += ' '
        else:
            clean_string += char
    return clean_string


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

    if fuzz.token_set_ratio(text, pokemon_name) > 83:
        return True
    return False


def extract_generations(generation_string):
    ''' Extracts generations and ranges from strings in format 'n' or 'n-n'.

    Args:
        generation_string (str): String that might be in format 'n' or 'n-n', eg. if the
            command is called like:
            
            !poke 1    -> [1]
            !poke 3-6  -> [3, 4, 5, 6]
            !poke      -> [1, 2, 3, 4, 5, 6, 7]
            !poke blah -> [1, 2, 3, 4, 5, 6, 7]

    Returns:
        list: Holds the gen number, or range of gens, or empty.
    '''

    all_generations = [1, 2, 3, 4, 5, 6, 7]

    if generation_string == 'all':
        return all_generations

    try:
        generation = int(generation_string)
        if generation in all_generations:
            return [generation]
    except ValueError:
        pass

    try:
        lower_bound, upper_bound = [int(i) for i in generation_string.split('-')]

        min_ = min(all_generations)
        if lower_bound < min_:
            lower_bound = min_

        max_ = max(all_generations)
        if upper_bound > max_:
            upper_bound = max_

        if upper_bound > lower_bound:
            return [*range(lower_bound, upper_bound + 1)]

    except ValueError:
        pass

    return all_generations



# ---------- Classes -----------
class Match():
    ''' A given game of WTP.

    Attributes:
        ctx (discord.ext.commands.context.Context): Discord context.
        generations (list): The pokemon generation numbers that a user restricts the match to.
        server (discord.guild.Guild): The server where the playing channel is.
        channel (discord.channel.TextChannel): The channel where the match is played.
        match_ended (bool): True if match is finished, False if not. Used to make sure
            endings only occur once per match.

        pokemon_name (str): The pokemon's name that players will guess at.
        unshrouded_path (str): The file path to the unshrouded WTP image.
        shrouded_path (str): The file path to the shrouded WTP image.

        messages (dict): Contains 'sections' as keys, and 'text' for each section as
            values. To be used by send_message and related functions.
    '''

    def __init__(self, ctx, generation_string):
        self.ctx = ctx
        self.generations = extract_generations(generation_string)
        self.server = ctx.guild
        self.channel = ctx.channel
        self.match_ended = False

        poke_data = get_pokemon_and_image(self.generations)
        self.pokemon_name = poke_data['name']
        self.unshrouded_path = poke_data['unshrouded_path']
        self.shrouded_path = poke_data['shrouded_path']
        
        self.messages = {}

        print(self.pokemon_name)


    async def send_message(self, text=str(), *, section, file=None):
        ''' Sends a message, or replaces the message if the section is already used. '''
        if section in self.messages.keys():
            _id = await self.messages[section].edit(content=text)
        else:
            _id = await self.ctx.send(text, file=file)
            self.messages[section] = _id


    async def append_to_message(self, *, text, section):
        ''' Appends to message. If a full edit needed, see send_message. '''
        message = self.messages[section]
        await message.edit(content=f'{message.content}{text}')


    async def set_timer(self, seconds):
        await asyncio.sleep(seconds)

        if not self.match_ended:
            await self.end('failure')


    async def start(self):
        silly_intro_texts = [
            "Do you wanna be the very best?! Then see how you fair in a match of",
            "Are you ready for",
            f"{self.ctx.message.author.name}! I choose you to play",
            "New Pokémon, who dis?",
            "Hi! You have 35 second to tell me"
        ]

        intro_text = f"*{random.choice(silly_intro_texts)}* ***WHO'S THAT POKÉMON?***"

        await self.send_message(text=intro_text, file=discord.File(self.shrouded_path), section='shrouded_image')
        await self.set_timer(35)


    async def end(self, nature, winner=str()):
        ''' Ends a match.

        Args:
            nature (str): 'success' if match won in time, 'failure' if not.
        '''
        self.match_ended = True

        if nature == 'failure':
            await self.send_message(f"Time's up! It's {self.pokemon_name}!",
                    section='end', file=discord.File(self.unshrouded_path))

        elif nature == 'success':
            await self.send_message(f"That's right, {winner.mention}! It's {self.pokemon_name}!",
                    section='end', file=discord.File(self.unshrouded_path))

        await self.messages['shrouded_image'].delete()
        del matches[self.channel.id]



# ---------- Globals -----------
bot = commands.Bot(command_prefix="!")
matches = {}



# ---------- Commands ----------
@bot.command()
async def poke(ctx, *, generation_string='all'):
    matches[ctx.message.channel.id] = Match(ctx, generation_string=generation_string)
    await matches[ctx.message.channel.id].start()


@bot.command()
async def d(ctx):
    print(bot.guilds)
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
            await match.end('success', winner=message.author)

    # Stops on_message from blocking all other commands.
    await bot.process_commands(message)



bot.run(client_secret)


