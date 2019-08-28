#!/usr/bin/python3.6
 
import discord

import bs4 as bs
import requests
import shutil

from random import choice
from time import sleep

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


client = discord.Client()

@client.event
async def on_ready():
    channel = client.get_channel(615344063205605434)
    fetch_image(get_random_name(names))
    await channel.send(file=discord.File('img.jpg'))

client.run(client_secret)
