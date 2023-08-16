# TODO: Finish notify users implementation, write methods to pass into Course constructor.
# TODO: Backup data to file using pickle and load on startup.
# TODO: Add type hints and clean code.

import discord
import json

from discord.ext import commands, tasks

from course import Course


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
courses = {}
TOKEN = ''
channel = None

with open('config.json', 'r') as f:
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
        await ctx.send(
            f'{ctx.author.mention} command not found. Use !help for a list of commands.'
        )
    else:
        raise error


@bot.command(
    name='add', help='Add courses to your watchlist. Enter CRNs separated by spaces.'
)
async def add(ctx, *args):
    user = ctx.message.author.mention
    for arg in args:
        if arg in courses:
            if user in courses[arg].users:
                await ctx.send(f'{ctx.author.mention} you are already watching {arg}.')
            else:
                courses[arg].add_user(user)
                await ctx.send(f'{ctx.author.mention} added {arg} to watchlist.')
        else:
            try:
                course = Course(arg)
                course.add_user(user)
                courses[arg] = course
                await ctx.send(f'{ctx.author.mention} added {arg} to watchlist.')
            except:
                await ctx.send(f'{ctx.author.mention} {arg} is not a valid CRN.')


@bot.command(
    name='remove',
    help='Remove courses from your watchlist. Enter CRNs separated by spaces.',
)
async def remove(ctx, *args):
    user = ctx.message.author.mention
    for arg in args:
        if arg in courses:
            if user in courses[arg].users:
                courses[arg].remove_user(user)
                await ctx.send(f'{ctx.author.mention} removed {arg} from watchlist.')
            else:
                await ctx.send(f'{ctx.author.mention} you are not watching {arg}.')
        else:
            await ctx.send(f'{ctx.author.mention} {arg} is not being watched.')


@bot.command(name='list', help='List all courses on your watchlist.')
async def list(ctx):
    watching = set()
    for course in courses.values():
        if course.has_user(ctx.author.mention):
            watching.add(course.crn)
    if len(watching) == 0:
        await ctx.send(f'{ctx.author.mention} you have no courses on your watchlist.')
    else:
        await ctx.send(f'{ctx.author.mention} you are watching {", ".join(watching)}.')


@bot.command(name='clear', help='Clear all courses from your watchlist.')
async def clear(ctx):
    for course in courses.values():
        if course.has_user(ctx.message.author.mention):
            course.remove_user(ctx.message.author.mention)
    await ctx.send(f'{ctx.author.mention} cleared watchlist.')


@tasks.loop(seconds=1)
async def notify_users():
    for course in courses.values():
        await course.update()


bot.run(TOKEN)
