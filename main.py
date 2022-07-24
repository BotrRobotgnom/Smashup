import discord
import os
from discord.ext import commands
from discord import default_permissions, option

from config import settings

bot = commands.Bot(command_prefix=settings['PREFIX'], intents=discord.Intents.all())

bot.remove_command('help')

cogs_listt = []

def auto_cogserr_load(key: str = None):
    if key == None:
        for cogss in os.listdir("./cogs"):
            if cogss == "__pycache__":
                continue
            if cogss.endswith(".py"):
                print(f"cogs.{cogss[:-3]}")
                bot.load_extension(f"cogs.{cogss[:-3]}")
                #lister
                cogs_listt.append(cogss[:-3])
            else:
                for cog in os.listdir(f"./cogs/{cogss}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        print(f"cogs.{cogss}.{cog[:-3]}")
                        bot.load_extension(f"cogs.{cogss}.{cog[:-3]}")
                        #lister
                        cogs_listt.append(cog[:-3])
    else:
        for cogss in os.listdir("./cogs"):
            if cogss == "__pycache__":
                continue
            if cogss.endswith(".py"):
                if str(cogss[:-3]) == key:
                    print(f"cogs.{cogss[:-3]}")
                    bot.load_extension(f"cogs.{cogss[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogss}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        if str(cog[:-3]) == key:
                            print(f"cogs.{cogss}.{cog[:-3]}")
                            bot.load_extension(f"cogs.{cogss}.{cog[:-3]}")


def auto_cogserr_unload(key: str = None):
    if key == None:
        for cogss in os.listdir("./cogs"):
            if cogss == "__pycache__":
                continue
            if cogss.endswith(".py"):
                print(f"cogs.{cogss[:-3]}")
                bot.unload_extension(f"cogs.{cogss[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogss}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        print(f"cogs.{cogss}.{cog[:-3]}")
                        bot.unload_extension(f"cogs.{cogss}.{cog[:-3]}")
    else:
        for cogss in os.listdir("./cogs"):
            if cogss == "__pycache__":
                continue
            if cogss.endswith(".py"):
                if str(cogss[:-3]) == key:
                    print(f"cogs.{cogss[:-3]}")
                    bot.unload_extension(f"cogs.{cogss[:-3]}")
            else:
                for cog in os.listdir(f"./cogs/{cogss}"):
                    if cog == "__pycache__":
                        continue
                    if cog.endswith(".py"):
                        if str(cog[:-3]) == key:
                            print(f"cogs.{cogss}.{cog[:-3]}")
                            bot.unload_extension(f"cogs.{cogss}.{cog[:-3]}")


@bot.event
async def on_ready():
    print('Бот запустился')

@bot.command()
async def cload(ctx, extension):
    if ctx.author.id == 318805947084439552:
        auto_cogserr_load(extension)
        await ctx.send(f"Cogs {extension} загружен")
    else:
        await ctx.send("!ОТКАЗАНО!")
    await ctx.channel.purge(limit=2)


@bot.command()
async def cunload(ctx, extension):
    if ctx.author.id == 318805947084439552:
        auto_cogserr_unload(extension)
        await ctx.send(f"Cogs {extension} отгружен")
    else:
        await ctx.send("!ОТКАЗАНО!")
    await ctx.channel.purge(limit=2)


@bot.command()
async def cre(ctx, extension: str = None):
    if ctx.author.id == 318805947084439552:
        auto_cogserr_unload(extension)
        auto_cogserr_load(extension)
        if extension != None:
            await ctx.send(f"Cogs {extension} перезагружен")
        else:
            await ctx.send(f"Cogsы перезагружены")
    else:
        await ctx.send("!ОТКАЗАНО!")
    await ctx.channel.purge(limit=2)

auto_cogserr_load()
print(cogs_listt)

@bot.slash_command(guild_ids = [485839030286549002],name ="cre", description="cogs")
@default_permissions(administrator=True)
@option("cog", description="cog", choices=cogs_listt)
async def slash__cre(ctx,cog: str):
    if ctx.user.id == (318805947084439552): 
        if cog != None:
            try:
                auto_cogserr_unload(cog)
            except:
                print(f"Cog не отгружается {cog}")
            try:
                auto_cogserr_load(cog)
            except:
                print(f"Cog не загружается {cog}")
            return await ctx.respond(f"Cog {cog} перезагружен", ephemeral=True)
        else:
            return await ctx.respond(f"Cog не указан", ephemeral=True)
    else:       
        return await ctx.respond("Ты кто?????", ephemeral=True)

bot.run(settings['TOKEN'])
