# TODO: Backup data to file using pickle and load on startup.
# TODO: Allow users to configure notifications.

import discord
import json

from discord.ext import commands, tasks

from course import Course


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
courses = {}
TOKEN = ''
CHANNEL = None
TERM = None

with open('config.json', 'r') as f:
    config = json.load(f)
    TOKEN = config['token']
    CHANNEL = config['channel']
    TERM = config['term']


@bot.event
async def on_ready():
    await bot.get_channel(CHANNEL).send('Bot connected.')
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
    notify_users.cancel()
    user = ctx.author.mention
    for crn in args:
        if crn in courses:
            if courses[crn].has_user(user):
                await ctx.send(f'{ctx.author.mention} you are already watching {crn}.')
            else:
                courses[crn].add_user(user)
                await ctx.send(f'{ctx.author.mention} added {crn} to watchlist.')
        else:
            try:
                course = Course(crn, TERM, waitlist_notify, seat_notify)
                course.add_user(user)
                courses[crn] = course
                await ctx.send(f'{ctx.author.mention} added {crn} to watchlist.')
            except ValueError as e:
                await ctx.send(f'{ctx.author.mention} {e}')
    notify_users.restart()


@bot.command(
    name='remove',
    help='Remove courses from your watchlist. Enter CRNs separated by spaces.',
)
async def remove(ctx, *args):
    notify_users.cancel()
    user = ctx.author.mention
    for crn in args:
        if crn in courses:
            if courses[crn].has_user(user):
                courses[crn].remove_user(user)
                await ctx.send(f'{ctx.author.mention} removed {crn} from watchlist.')
            else:
                await ctx.send(f'{ctx.author.mention} you are not watching {crn}.')
        else:
            await ctx.send(f'{ctx.author.mention} {crn} is not being watched.')
    notify_users.restart()


@bot.command(name='list', help='List all courses on your watchlist.')
async def list(ctx):
    notify_users.cancel()
    watching = set()
    for course in courses.values():
        if course.has_user(ctx.author.mention):
            watching.add(course.crn)
    if len(watching) == 0:
        await ctx.send(f'{ctx.author.mention} you have no courses on your watchlist.')
    else:
        await ctx.send(f'{ctx.author.mention} you are watching {", ".join(watching)}.')
    notify_users.restart()


@bot.command(name='clear', help='Clear all courses from your watchlist.')
async def clear(ctx):
    notify_users.cancel()
    for course in courses.values():
        if course.has_user(ctx.author.mention):
            course.remove_user(ctx.author.mention)
    await ctx.send(f'{ctx.author.mention} cleared watchlist.')
    notify_users.restart()

@tasks.loop(seconds=1)
async def notify_users():
    for course in courses.values():
        await course.update()


async def waitlist_notify(course):
    await bot.get_channel(CHANNEL).send(
        f'Waitlist available: {course}. {course.user_mentions()}'
    )


async def seat_notify(course):
    await bot.get_channel(CHANNEL).send(
        f'Seat available: {course}. {course.user_mentions()}'
    )


bot.run(TOKEN)
