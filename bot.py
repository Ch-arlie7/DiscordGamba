import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import sys
from datetime import datetime
from gamba import Gamba
from economy import Economy

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
user = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_DATABASE')
admin_id = int(os.getenv('ADMIN_ID'))

stimmy_amount_per_day = 10
PREFIX = '!'
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
guilds = {}
allowed_guilds = ["Charlie's Server", "Swedistan"]

def idMappedToAlphabet(n):
    """To convert guild ID into a valid SQL table name

    Args:
        n (int): guild id

    Returns:
        str: str guild id
    """    

    d = {'0': 'a',
         '1': 'b',
         '2': 'c',
         '3': 'd',
         '4': 'e',
         '5': 'f',
         '6': 'g',
         '7': 'h',
         '8': 'i',
         '9': 'j'}
    return ''.join([d[x] for x in str(n)])

@bot.event
async def on_ready():
    print('Connected to {}'.format(', '.join([x.name for x in bot.guilds])))
    todays_date = datetime.today().strftime('%Y-%m-%d')
    for guild in bot.guilds:
        table = idMappedToAlphabet(guild.id)
        economy = Economy(user, password, host, port, database, table)
        economy.createTable()
        for member in guild.members:
            economy.insertRow(member.id, member.name, todays_date)
            economy.updateName(member.id, member.name)
        economy.refundAll()
        economy.applyStimmy(stimmy_amount_per_day)
        print(economy.table)
        print()
        economy.showTable()
        print('-------------')
        guilds[table] = economy
    print('Success')

@bot.command()
async def leave(ctx):
    if ctx.message.author.id == admin_id:   
        await ctx.message.add_reaction('👌')
        sys.exit()
    await ctx.message.add_reaction('⛔')
    return

@bot.command()
async def flip(ctx, amount): 
    if ctx.message.guild.name not in allowed_guilds:
        return    
    try: 
        amount = int(amount)
    except: 
        await ctx.message.add_reaction('❓')
        return
    if amount <= 0:
        await ctx.message.add_reaction('🤡')
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    
    if not e.sufficientBalance(ctx.message.author.id, amount):
        await ctx.message.add_reaction('🚫')
        await ctx.message.add_reaction('💵')
        return
    if e.flip(ctx.message.author.id, amount):
        await ctx.message.add_reaction('🥳')
        return
    else: 
        await ctx.message.add_reaction('💩')
        return

@bot.command()
async def tip(ctx, receiver, amount):
    if ctx.message.guild.name not in allowed_guilds:
        return
    try:
        receiver = int(receiver[3:-1])
        amount = int(amount)
    except:
        await ctx.message.add_reaction('❓')
        return
    
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    if not e.sufficientBalance(ctx.message.author.id, amount):
        await ctx.message.add_reaction('🚫')
        await ctx.message.add_reaction('💵')
        return
    if amount <= 0:
        await ctx.message.add_reaction('🤡')
        return
    if not e.isValidDiscordID(receiver):
        await ctx.message.add_reaction('🤡')
        return
    if e.sendTip(ctx.message.author.id, receiver, amount):
        await ctx.message.add_reaction('🤩')
        return 
    await ctx.message.add_reaction('👎')
    return

@bot.command()
async def points(ctx):
    if ctx.message.guild.name not in allowed_guilds:
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    points = e.selectPoints(ctx.message.author.id)
    embed = discord.Embed(title = '**{}**'.format(points),
                          color=discord.Color.blue())   
    await ctx.send(embed=embed)
    return

@bot.command()
async def leaderboard(ctx):
    if ctx.message.guild.name not in allowed_guilds:
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    stats = e.leaderboardStats()
    if not stats:
        await ctx.message.add_reaction('😦')
        return
    embed = discord.Embed(title='**Leaderboard**',
                          color=discord.Color.red())
    f_name = stats['names'].pop(0)
    f_points = stats['points'].pop(0)

    leaderboard_string = ''
    for i, v in enumerate(stats['names']):
        leaderboard_string += '{}. {}  -  {}\n'.format(i+2, v, stats['points'][i])
    if leaderboard_string == '':
        leaderboard_string = '______________________'
    embed.add_field(name='1. {}  -  {}'.format(f_name, f_points), value=leaderboard_string, inline=False)
    await ctx.send(embed=embed)
    return
    
@bot.command()
async def gamba(ctx, title: str, *args):
    '''Example: !gamba "can these morons figure it out?" yes no "definitely not" probably'''
    if ctx.message.guild.name not in allowed_guilds:
        return
    
    print(args)
    print(type(args))
    if len(args) >= 10 or len(args) <= 1:
        await ctx.message.add_reaction('🤡')
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    details = e.createNewGamba(ctx.message.author.id, title, args)

    embed = discord.Embed(title='**{}**'.format(title),
                          color = discord.Color.blue())
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)   

    for i, v in enumerate(details['options_alpha']):
        embed.add_field(name=v, value=details['options'][i], inline=False)
    embed.set_footer(text='____________\nID = {}\nExample: !bet {} A 400'.format(details['id'], details['id']))
    await ctx.send(embed=embed)
    return

#addbet
#endbet
#cancelbet


bot.run(token)










