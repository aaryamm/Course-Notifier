# TODO: Backup data to file using pickle and load on startup.
# TODO: Make sure course exists before watching.
# TODO: Print more data about course when watching like name and section.

import discord
import json
from discord.ext import commands, tasks


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
users = {}
courses = {}
TOKEN = ''
channel = None

with open ('config.json', 'r') as f:
    config = json.load(f)
    TOKEN = config['token']
    channel = config['channel']


@bot.event
async def on_ready():
    await bot.get_channel(channel).send('Bot connected.')
    notify_users.start()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send(f'{ctx.author.mention} command not found. Use !help for a list of commands.')
    else:
        raise error


@bot.command(name='add', help='Add courses to your watchlist. Enter CRNs separated by spaces.')
async def add(ctx, *args):
    new_courses = set()
    for arg in args:
        if len(str(arg)) != 5 or not arg.isdigit():
            await ctx.send(f'{ctx.author.mention} {arg} is not a valid CRN.')
        elif arg in users.get(ctx.author, set()):
            await ctx.send(f'{ctx.author.mention} you are already watching {arg}.')
        else:
            new_courses.add(arg)
            courses[arg] = courses.get(arg, set()) | {ctx.author}
    if len(new_courses) == 0:
        await ctx.send(f'{ctx.author.mention} no valid new CRNs were entered.')
    else:
        users[ctx.author] = users.get(ctx.author, set()) | new_courses
        await ctx.send(f'{ctx.author.mention} added {", ".join(new_courses)} to watchlist.')


@bot.command(name='remove', help='Remove courses from your watchlist. Enter CRNs separated by spaces.')
async def remove(ctx, *args):
    removed_courses = set()
    for arg in args:
        if len(str(arg)) != 5 or not arg.isdigit():
            await ctx.send(f'{ctx.author.mention} {arg} is not a valid CRN.')
        elif arg not in users.get(ctx.author, set()):
            await ctx.send(f'{ctx.author.mention} you are not watching {arg}.')
        else:
            removed_courses.add(arg)
            courses[arg] = courses.get(arg, set()) - {ctx.author}
            if courses[arg] == set():
                del courses[arg]
    if len(removed_courses) == 0:
        await ctx.send(f'{ctx.author.mention} no valid existing CRNs were entered.')
    else:
        users[ctx.author] = users.get(
            ctx.author, set()) - removed_courses
        if users[ctx.author] == set():
            del users[ctx.author]
        await ctx.send(f'{ctx.author.mention} removed {", ".join(removed_courses)} from watchlist.')


@bot.command(name='list', help='List all courses on your watchlist.')
async def list(ctx):
    if ctx.author not in users:
        await ctx.send(f'{ctx.author.mention} you have no courses on your watchlist.')
    else:
        await ctx.send(f'{ctx.author.mention} you are watching {", ".join(users[ctx.author])}.')


@bot.command(name='watchers', help='List all users watching a course. Enter CRNs separated by spaces.')
async def watchers(ctx, *args):
    num_courses = 0
    for arg in args:
        if len(str(arg)) != 5 or not arg.isdigit():
            await ctx.send(f'{ctx.author.mention} {arg} is not a valid CRN.')
        elif arg not in courses:
            await ctx.send(f'{ctx.author.mention} {arg} is not being watched.')
            num_courses += 1
        else:
            names = {user.name for user in courses[arg]}
            await ctx.send(f'{ctx.author.mention} {arg} is being watched by {", ".join(names)}.')
            num_courses += 1
    if num_courses == 0:
        await ctx.send(f'{ctx.author.mention} no valid watched CRNs were entered.')


@bot.command(name='clear', help='Clear all courses from your watchlist.')
async def clear(ctx):
    if ctx.author not in users:
        await ctx.send(f'{ctx.author.mention} you have no courses on your watchlist.')
    else:
        for course in users[ctx.author]:
            courses[course] = courses.get(
                course, set()) - {ctx.author}
            if courses[course] == set():
                del courses[course]
        del users[ctx.author]
        await ctx.send(f'{ctx.author.mention} cleared watchlist.')


@tasks.loop(seconds=1)
async def notify_users():
    pass


bot.run(TOKEN)