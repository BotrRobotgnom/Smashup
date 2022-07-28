import discord
import os
from discord.ext import commands

from config import settings

bot = commands.Bot(command_prefix=settings['PREFIX'], intents=discord.Intents.all())

bot.remove_command('help')

cogs_list = []


def auto_cogs_err_load(key: str = None):
    if key is None:
        for cogs in os.listdir("./cogs"):
            if cogs == "__pycache__":
                continue

            if cogs.endswith(".py"):
                print(f"cogs.{cogs[:-3]}")
                bot.load_extension(f"cogs.{cogs[:-3]}")
                cogs_list.append(cogs[:-3])
            else:
                for cog in os.listdir(f"./cogs/{cogs}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        print(f"cogs.{cogs}.{cog[:-3]}")
                        bot.load_extension(f"cogs.{cogs}.{cog[:-3]}")
                        cogs_list.append(cog[:-3])

    else:
        for cogs in os.listdir("./cogs"):
            if cogs == "__pycache__":
                continue

            if cogs.endswith(".py"):
                if str(cogs[:-3]) == key:
                    print(f"cogs.{cogs[:-3]}")
                    bot.load_extension(f"cogs.{cogs[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogs}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        if str(cog[:-3]) == key:
                            print(f"cogs.{cogs}.{cog[:-3]}")
                            bot.load_extension(f"cogs.{cogs}.{cog[:-3]}")


def auto_cogs_err_unload(key: str = None):
    if key is None:
        for cogs in os.listdir("./cogs"):
            if cogs == "__pycache__":
                continue
            if cogs.endswith(".py"):
                print(f"cogs.{cogs[:-3]}")
                bot.unload_extension(f"cogs.{cogs[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogs}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        print(f"cogs.{cogs}.{cog[:-3]}")
                        bot.unload_extension(f"cogs.{cogs}.{cog[:-3]}")
    else:
        for cogs in os.listdir("./cogs"):
            if cogs == "__pycache__":
                continue
            if cogs.endswith(".py"):
                if str(cogs[:-3]) == key:
                    print(f"cogs.{cogs[:-3]}")
                    bot.unload_extension(f"cogs.{cogs[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogs}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        if str(cog[:-3]) == key:
                            print(f"cogs.{cogs}.{cog[:-3]}")
                            bot.unload_extension(f"cogs.{cogs}.{cog[:-3]}")


@bot.event
async def on_ready():
    print('Бот запустился')


auto_cogs_err_load()
print(cogs_list)


bot.run(settings['TOKEN'])
