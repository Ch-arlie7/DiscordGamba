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
allowed_guilds = ["Charlie's Server", "Swedistan", "Coconut Esports"]

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
    """50/50 (xd) double or nothing.
    Example: !flip 20
    """     
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
    """Transfer points.
    Example: !tip @Charlie 20
    """    
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
    if ctx.message.author.id == receiver:
        await ctx.message.add_reaction('🤡')
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
    """Show current points.
    Example: !points
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    points = e.selectPoints(ctx.message.author.id)

    await ctx.send('```\n{}```'.format(points))
    return

@bot.command()
async def leaderboard(ctx):
    """Show current leaderboard of active degen gamblers.
    Example: !leaderboard
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    stats = e.leaderboardStats()
    if not stats:
        await ctx.message.add_reaction('😦')
        return

    output = '```\nLeaderboard\n\n'
    for i, v in enumerate(stats['names']):
        output += '{}. {} - {}\n'.format(i+1, v, stats['points'][i])
    output += '```'
    await ctx.send(output)
    return
    
@bot.command()
async def gamba(ctx, title: str, *args):
    """Create a new Gamba. Use quotation marks for multi-word arguments.
    Example: !gamba "Will I finally win a soloq game?" Yes No "Obviously not" Maybe
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    if len(args) >= 10 or len(args) <= 1:
        await ctx.message.add_reaction('🤡')
        return
    args = [x[:25] for x in args]
    title = title[:200]
    
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    details = e.createNewGamba(ctx.message.author.id, title, args)

    output = '```\n{}\n\n'.format(title)
    for i, v in enumerate(details['options_alpha']):
        output += '{}. {}\n'.format(v, details['options'][i])
    output += '\nID = {} | Author = {}\n```'.format(details['id'], ctx.message.author.name)
    await ctx.send(output)
    return

@bot.command()
async def bet(ctx, _id, choice, amount):
    """Bet on an existing Gamba.
    Example: !bet 1 a 20
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    try:
        _id = int(_id)
        amount = int(amount)
        choice = (str(choice)).upper()
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
    if _id not in e.gambas:
        await ctx.message.add_reaction('❓')
        return  
    if ctx.message.author.id in e.gambas[_id].gamblers:
        await ctx.message.add_reaction('🚫')
        return
    if choice not in e.gambas[_id].options_alpha:
        await ctx.message.add_reaction('❓')
        return 
    if e.newBet(_id, ctx.message.author.id, ctx.message.author.name, choice, amount):
        await ctx.message.add_reaction('👍')
        return
    else:
        await ctx.message.add_reaction('👎')
        return

@bot.command()
async def end(ctx, _id, result):
    """Ends a Gamba. Only the Gamba's author has permission.
    Example: !end 1 b
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    try:
        _id = int(_id)
        result = (str(result)).upper()
    except: 
        await ctx.message.add_reaction('❓')
        return
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    if _id not in e.gambas:
        await ctx.message.add_reaction('❓')
        return 
    if ctx.message.author.id != e.gambas[_id].author:
        await ctx.message.add_reaction('🔞')
        return  
    if result not in e.gambas[_id].options_alpha:
        await ctx.message.add_reaction('❓')
        return
    data = e.closeBet(_id, result)
    if not data:
        await ctx.message.add_reaction('👎')
        return
    if data == 1:                                   # Clumsy handling of 'no winner' case 
        await ctx.message.add_reaction('👍')
        return

    output = '```\nWinners\n\n'
    for i, v in enumerate(data['winners']):
        output += '{} : {}\n'.format(v, data['winnings'][i])
    output += '```'
    await ctx.send(output)
    return
        

@bot.command()
async def cancel(ctx, _id):
    """Cancels a Gamba, refunding bets. Only the Gamba's author has permission.
    Example: !cancel 1
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    try:
        _id = int(_id)
    except:
        await ctx.message.add_reaction('❓')
        return 
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    if _id not in e.gambas:
        await ctx.message.add_reaction('❓')
        return
    if ctx.message.author.id != e.gambas[_id].author:
        await ctx.message.add_reaction('🔞')
        return  
    if e.cancelBet(_id):
        await ctx.message.add_reaction('👍')
        return
    else:
        await ctx.message.add_reaction('👎')
        return
        
@bot.command()
async def standings(ctx, _id):
    """Show standings on an existing Gamba
    Example: !standings 1
    """
    if ctx.message.guild.name not in allowed_guilds:
        return
    try:
        _id = int(_id)
    except:
        await ctx.message.add_reaction('❓')
        return 
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]
    if _id not in e.gambas:
        await ctx.message.add_reaction('❓')
        return
    data = e.gambas[_id].getStandings()
 
    output = '```\n{}\n\n'.format(e.gambas[_id].title)
    for i, v in enumerate(data['options']):
        output += '{}:   {} - {}%\n'.format(v, data['totals'][i], data['percent'][i])
    output += '```'
    await ctx.send(output)
    return

@bot.command()
async def gambas(ctx):
    """Shows titles and IDs of active Gambas
    Example: !gambas
    """
    e = guilds[idMappedToAlphabet(ctx.message.guild.id)]

    output = '```\nActive Gambas\n\n'
    for _id in e.gambas:
        output += '{}. ID = {}\n'.format(e.gambas[_id].title, _id)
    output += '```'
    await ctx.send(output)
    return

bot.run(token)










