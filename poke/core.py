#!/usr/bin/python3.6

from fuzzywuzzy import fuzz
import asyncio
import discord
from discord.ext import commands

import random

from helpers import get_pokemon_and_image, config


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


def too_many_matches_on_server(server):
    global current_servers

    if server is None:
        return False

    if current_servers.count(server) >= 3:
        return True

    return False


def too_many_matches_for_user(user):
    global current_users

    if current_users.count(user) >= 1:
        return True

    return False


def extract_generations(generation_string):
    ''' Extracts generations and ranges from strings in format 'n' or 'min-max'.

    Args:
        generation_string (str): String that might be in format 'n' or 'min-max', eg. if the
            command is called like:
            
            !poke 1    -> [1]
            !poke 3-6  -> [3, 4, 5, 6]
            !poke      -> [1, 2, 3, 4, 5, 6, 7]
            !poke blah -> [1, 2, 3, 4, 5, 6, 7]

    Returns:
        list: Holds the gen number, or range of gens, or empty.
    '''

    all_generations = [1, 2, 3, 4, 5, 6, 7]

    # string = 'all'
    if generation_string == 'all':
        return all_generations

    # format = 'n'
    try:
        generation = int(generation_string)
        if generation in all_generations:
            return [generation]
    except ValueError:
        pass

    # format = 'min-max'
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


async def change_status_task(primary_status, secondary_statuses):
    ''' Replaces the primary status with secondary ones ar small intervals.

    Args:
        primary_status (str): The 'game' that will be shown as a Discord status most often.
        secondary_statuses (list): Strings containing less important statuses.
    '''

    while True:
        for secondary_status in secondary_statuses:
            await bot.change_presence(activity=discord.Game('!poke  |  !poke-help'))
            await asyncio.sleep(30)
            await bot.change_presence(activity=discord.Game(secondary_status))
            await asyncio.sleep(10)


async def can_start_match(server_id, channel_id, user_id):
    ''' Checks if a requested match can be started. '''
    global matches

    if channel_id not in matches:
        if not too_many_matches_on_server(server_id):
            if not too_many_matches_for_user(user_id):
                return True
    return False



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
        cancellation_aborted (bool): If a match's cancellation has been aborted.

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
        self.cancellation_aborted = False

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


    async def ask_to_cancel(self, trigger_message):
        ''' Starts a cancellation timer to end match, allows users to cancel cancellation.

        Args:
            trigger_message (str): The message that triggered the cancellation process.
        '''

        # If a cancellation has already been vetoed, no use calling another cancellation
        # when there's so little time in a match anyway.
        if self.cancellation_aborted == False:
            message_text = '```Cancelling match in 5 seconds. Press on ❌ react to stop cancellation.\n' \
                    '(cancellations can only be called once per match).```'
            await self.send_message(f"> {trigger_message}\n{message_text}", section='cancel_dialogue')
            await self.messages['cancel_dialogue'].add_reaction('❌')
            await asyncio.sleep(5)
            await self.messages['cancel_dialogue'].delete()
            if self.cancellation_aborted == False:
                await self.end('failure')


    async def start(self):
        global current_servers
        global current_users

        if self.ctx.guild is not None:
            current_servers.append(self.ctx.guild.id)
        current_users.append(self.ctx.message.author.id)

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

        Sends a win or lose message, deletes the shrouded message, and deletes the match
        reference in matches (also current_users and current_servers).

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
        if self.ctx.guild is not None:
            current_servers.remove(self.ctx.guild.id)
        current_users.remove(self.ctx.message.author.id)



# ---------- Globals -----------
client_secret = open(config['token_dir']).read().replace('\n', '')

bot = commands.Bot(command_prefix="!")

matches = {}

# Used to limit user / server matches so they don't spam commands and cause an
# 'amplified DOS' attack
current_servers = []
current_users = []

primary_status = '!poke | !poke-help'
secondary_statuses = [
    "Who's That Pokemon?",
    "gitlab.com/rendello/",
    "!poke-help for help",
]



# ---------- Commands ----------
bot.remove_command('help')

@bot.command(aliases=['p'])
async def poke(ctx, *, generation_string='all'):

    # No server or channel IDs when being DM-ed
    server_id = ctx.guild.id if ctx.guild is not None else None
    channel_id = ctx.channel.id if ctx.channel is not None else None

    if await can_start_match(server_id=server_id, channel_id=channel_id, user_id=ctx.message.author.id):

        matches[ctx.message.channel.id] = Match(ctx, generation_string=generation_string)
        await matches[ctx.message.channel.id].start()


@bot.command(aliases=['h', 'poke-help', 'poke-h'])
async def help(ctx):
    await ctx.channel.send('```Pokebot is the "Who\'s That Pokemon" bot!\n\n'
            + '!poke       Play a match\n'
            + '!poke 1     Only use generation 1 Pokemon\n'
            + '!poke 2-4   Use generations 2 through 4\n\n'
            + '!poke-help  Show this dialogue\n\n'
            + 'type "cancel" or "idk" to cancel a match.```')


@bot.command()
async def d(ctx):
    print(bot.guilds)
    print(matches)



# ----------- Events -----------
@bot.event
async def on_ready():
    await bot.loop.create_task(change_status_task(primary_status, secondary_statuses))


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
        elif any(word in clean_message for word in ['cancel', 'idk']):
            await match.ask_to_cancel(trigger_message=message.content)

    # Stops on_message from blocking all other commands.
    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    global matches

    # All deals with reacting to cancellation messages
    if reaction.message.channel.id in matches.keys() and user.id != bot.user.id:
        match = matches[reaction.message.channel.id]

        if 'cancel_dialogue' in match.messages:
            if reaction.message.id == match.messages['cancel_dialogue'].id:
                match.cancellation_aborted = True

                # Bad
                await match.send_message('Cancellation aborted. ', section='cancel_dialogue')



# ------- Program Start --------
if __name__ == '__main__':
    bot.run(client_secret)
