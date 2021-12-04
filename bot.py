import asyncio
import logging
import os
from sys import stderr, stdout

from dis_snek.client import Snake
from dis_snek.const import logger_name
from dis_snek.models import slash_command, InteractionContext, listen
from dis_snek.models.enums import Intents

from dotenv import load_dotenv


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)s] [%(name)s]: %(message)s', '%H:%M:%S')

    # file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w+')
    # file_handler.setLevel(logging.DEBUG)
    # file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


logger = get_logger(logger_name)

intents = Intents.ALL
# intents.MESSAGES = True
# intents.GUILD_MEMBERS = True
# intents.GUILD_PRESENCES = False
bot = Snake(intents=intents, default_prefix='.', sync_interactions=True, debug_scope=910984528351338557)


@slash_command(name='ping', description='Pong!')
async def ping(ctx: InteractionContext):
    await ctx.send('Pong!')


@listen()
async def on_ready():
    print('Ready!')


# # Needed for proper things
# async def main():
#     bot.grow_scale('group_manager')
#     load_dotenv()
#     await bot.login(os.getenv('TOKEN'))
#
# asyncio.run(main())

bot.grow_scale('group_manager')
load_dotenv()
bot.start(os.getenv('TOKEN'))
