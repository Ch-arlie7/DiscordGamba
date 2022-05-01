import discord
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
import sys
from datetime import datetime
from economy import Economy
import time


    #### MAYBE ALTER GAMBA TO MAKE IT CANCEL IF NO WINNERS? WOULD TAKE REWRITE OF THE FUNCTION. 

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
admin_id = int(os.getenv('ADMIN_ID'))
stimmy_amount_per_day = int(os.getenv('STIMMY_AMOUNT'))

PREFIX = '!'
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
guilds = {}

def guild_id_adjusted(id: int)->str:
    '''Create valid, unique SQL db name'''
    return 'db' + str(id)

@tasks.loop(hours=6.0)
async def update_economies():
    todays_date = datetime.today().strftime('%Y-%m-%d')
    for guild in bot.guilds:
        e = guilds[guild_id_adjusted(guild.id)]
        e.apply_stimmy()
        for member in guild.members:
            e.insert_user(member.id, member.name, todays_date)
            e.update_username(member.id, member.name)
    print('Updated Successfully')

@bot.event
async def on_ready():
    start = time.time()
    print('Connected to {}'.format(', '.join([x.name for x in bot.guilds])))
    todays_date = datetime.today().strftime('%Y-%m-%d')
    for guild in bot.guilds:
        database = guild_id_adjusted(guild.id)
        economy = Economy(database)
        for member in guild.members:
            economy.insert_user(member.id, member.name, todays_date)
        guilds[database] = economy
    t = round(time.time() - start, 2)
    print('Initializing took: {}s'.format(t))

@bot.event
async def on_member_join(member):
    '''Experimental completely untested lol'''
    todays_date = datetime.today().strftime('%Y-%m-%d')
    e = guilds[guild_id_adjusted(member.guild.id)]
    e.insert_user(member.id, member.name, todays_date)
    print('Member just joined.\nID: {}\nName: {}'.format(member.id, member.name))


# @bot.command()
# async def leave(ctx):
#     if ctx.message.author.id == admin_id:   
#         await ctx.message.add_reaction('👌')
#         sys.exit()
#     await ctx.message.add_reaction('⛔')
#     return

@bot.command()
async def points(ctx):
    """Show current points.
    Example: !points
    """
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    points = e.select_row_by_id('points', ctx.message.author.id)[0]
    await ctx.send('```\n{}```'.format(points))
    return

@bot.command()
async def leaderboard(ctx):
    """Show current leaderboard of active degen gamblers.
    Example: !leaderboard
    """
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    stats = e.get_leaderboard_stats() # [(username, points), ...]
    s = 'Leaderboard\n'
    for gambler in stats:
        line = '\n{} - {}'.format(gambler[0], gambler[1])
        s += line
    await ctx.send('```\n{}```'.format(s))
    return

@bot.command()
async def flip(ctx, amount):
    """50/50 double or nothing.
    Example: !flip 20
    """     
    try:
        amount = int(amount)
    except: 
        await ctx.message.add_reaction('❓')
        return
    if amount <= 0:
        await ctx.message.add_reaction('🤡')
        return
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]

    if not e.sufficient_balance(ctx.message.author.id, amount):
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
    try:
        receiver = int(''.join([x for x in receiver if x.isnumeric()]))
        amount = int(amount)
    except:
        await ctx.message.add_reaction('❓')
        return
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    if not e.sufficient_balance(ctx.message.author.id, amount):
        await ctx.message.add_reaction('🚫')
        await ctx.message.add_reaction('💵')
        return
    if ctx.message.author.id == receiver or amount <= 0 or not e.is_valid_discord_id(receiver):
        await ctx.message.add_reaction('🤡')
        return
    if e.send_tip(ctx.message.author.id, receiver, amount):
        await ctx.message.add_reaction('🤩')
        return 
    await ctx.message.add_reaction('👎')
    return

@bot.command()
async def gamba(ctx, title, *args):
    """Create a new Gamba. Use quotation marks for multi-word arguments.
    Example: !gamba "Will TSM ever win a game?" Yes No "Obviously not" Maybe
    """
    if len(args) >= 10 or len(args) <= 1:
        await ctx.message.add_reaction('🤡')
        return
    args = [x[:25] for x in args] # to avoid abuse
    title = title[:200]
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    details = e.create_new_gamba(ctx.message.author.id, title, args)

    output = '```\n{}\n\n'.format(title)
    for i, v in enumerate(details['options_alpha']):
        output += '{}. {}\n'.format(v, details['options'][i])
    output += '\nID = {} | Author = {}\n```'.format(details['id'], ctx.message.author.name)
    await ctx.send(output)
    return

@bot.command()
async def bet(ctx, g_id, choice, amount):
    """Bet on an existing Gamba.
    Example: !bet 1 a 20
    """
    try:
        g_id = int(g_id)
        amount = int(amount)
        choice = (str(choice)).upper()
    except: 
        await ctx.message.add_reaction('❓')
        return
    if amount <= 0:
        await ctx.message.add_reaction('🤡')
        return  
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    if not e.sufficient_balance(ctx.message.author.id, amount):
        await ctx.message.add_reaction('🚫')
        await ctx.message.add_reaction('💵')
        return
    if not e.is_valid_g_id(g_id) or not e.is_valid_choice(g_id, choice):
        await ctx.message.add_reaction('❓')
        return   
    if e.has_already_bet(g_id, ctx.message.author.id):
        await ctx.message.add_reaction('🚫')
        return
    if e.add_bet(g_id, ctx.message.author.id, ctx.message.author.name, choice, amount):
        await ctx.message.add_reaction('👍')
        return
    else:
        await ctx.message.add_reaction('👎')
        return

@bot.command()
async def end(ctx, g_id, result):
    """Ends a Gamba. Only the Gamba's author has permission.
    Example: !end 1 b
    Alternatively cancel a Gamba. 
    Example: !end 1 cancel
    """
    try:
        g_id = int(g_id)
        result = (str(result)).upper()
    except:          
        await ctx.message.add_reaction('❓')
        return
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    if not e.is_valid_g_id(g_id):
        await ctx.message.add_reaction('❓')
        return
    if not e.is_author(g_id, ctx.message.author.id):
        await ctx.message.add_reaction('🚫')
        return 
    if result == 'CANCEL':
        e.cancel_bet(g_id)
        await ctx.message.add_reaction('👍')
        return
    if not e.is_valid_choice(g_id, result):
        await ctx.message.add_reaction('❓')
        return
    data = e.close_bet(g_id, result)

    output = '```\nWinners\n\n'
    for i, v in enumerate(data['winner_names']):
        output += '{} : {}\n'.format(v, data['winnings'][i])
    output += '```'
    await ctx.send(output)
    return


@bot.command()
async def standings(ctx, g_id):
    """Show standings on an existing Gamba
    Example: !standings 1
    """
    try:
        g_id = int(g_id)
    except:          
        await ctx.message.add_reaction('❓')
        return
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    if not e.is_valid_g_id(g_id):
        await ctx.message.add_reaction('❓')
        return
    data = e.gamba_standings(g_id)
    output = data['title'] + '\n'

    for i, v in enumerate(data['options']):
        output += '\n{}:  {} - {}%'.format(v, data['totals'][i], data['percent'][i])
    output = '```\n' + output + '```'
    await ctx.send(output)
    return

@bot.command()
async def gambas(ctx):
    """Shows titles and IDs of active Gambas
    Example: !gambas
    """
    e = guilds[guild_id_adjusted(ctx.message.guild.id)]
    data = e.active_gambas()
    output = '```\nActive Gambas\n'
    for id in data:
        output += '\n{} - ID: {}'.format(data[id], id)
    output += '\n```'
    await ctx.send(output)
    return

if __name__ == '__main__':
    bot.run(token)








