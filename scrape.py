#!/usr/bin/python3.6
 
import discord
from discord.ext import commands

import bs4 as bs
import requests
import shutil
import urllib.request

from random import choice
from time import sleep
import re

from names import names
from secret_token import client_secret


def scrape_names():
    url = 'https://pokemondb.net/pokedex/national'
    headers = {'User-Agent':'Mozilla/5.0'}
    page = requests.get(url, headers=headers)

    soup = bs.BeautifulSoup(page.text, 'html5lib')

    names = []
    name_tags = soup.find_all(class_="ent-name")
    for name in name_tags:
        names.append(name.string)

    return names


def fetch_image(name):
    name = name.lower()
    name = name.replace(' ', '-')

    url = f'https://img.pokemondb.net/artwork/large/{name}.jpg'
    headers = {'User-Agent':'Mozilla/5.0'}
    response = requests.get(url, stream=True, headers=headers)
    with open('img.jpg', 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


def get_random_name(names):
    return choice(names)


def match_numbers_and_pokemon():
    source = urllib.request.urlopen(f"https://www.pokemon.com/us/pokedex/").read()
    soup = bs.BeautifulSoup(source, 'lxml')

    cards = soup.find_all('li')
    print(cards)
    for card in cards:
        print(card.text)
        print()


match_numbers_and_pokemon()


#bot = commands.Bot(command_prefix='!')
#
#
#@bot.command()
#async def poke(ctx):
#    match_numbers_and_pokemon()
#
#
#@bot.command()
#async def o(ctx):
#    fetch_image(get_random_name(names))
#    await ctx.channel.send(file=discord.File('img.jpg'))
#
#bot.run(client_secret)
