import json
import discord
from discord.ext import commands, tasks
from discord.commands import option
import requests
from sqlfunc import sql_py
from discord.ui import View, Select
from regexs import *


def voice_check(interaction, voice_client):
    if interaction.user.voice:
        if voice_client:
            if interaction.user.voice.channel != voice_client.channel:
                return ["respond", "Бот уже находится в другом канале!"]
            else:
                return ["voice", voice_client]
        else:
            return ["voice", None]
    else:
        return ["respond", "Для начала зайдите в голосовой канал!"]


def classic_embed(emb_list):
    # embed, author, fields, image, footer, thumbnail
    emb = emb_list[0]
    if emb_list[1]:
        emb.set_author(name=emb_list[1][0], url=emb_list[1][1], icon_url=emb_list[1][2])
    if emb_list[2]:
        emb.set_image(emb_list[2][0])
    if emb_list[3]:
        emb.set_footer(text=emb_list[3][0], icon_url=emb_list[3][1])
    if emb_list[4]:
        emb.set_thumbnail(url=emb_list[4][0])
    return emb


def get_noun_ending(number, words):
    if len(words) == 3:
        return words[2 if (4 < number % 100 < 20) else [2, 0, 1, 1, 1, 2][
            abs(number) % 10 if (number % 10 < 5) else 5]]


async def add_to_play(voice_client, interaction, mashup_list):
    all_get = sql_py("get", [interaction.guild.id])
    new_next = json.loads(all_get['next_play'])
    for i in mashup_list:
        new_next.append(i)
    sql_py("update_next", [interaction.guild.id, json.dumps(new_next)])
    if not voice_client.is_playing():
        stop_check_lister.append([0, [voice_client, interaction]])


stop_check_lister = []


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
COOKIES = {'token': '7f5bc728-1019-4ca0-ac89-de77c2d868f1'}


async def play_global(voice_client, interaction):
    all_get = sql_py("get", [interaction.guild.id])
    back_play = json.loads(all_get['back_play'])
    now_play = json.loads(all_get['now_play'])
    next_play = json.loads(all_get['next_play'])
    if not next_play:
        return
    
    if now_play:
        back_play.insert(0, now_play.copy())
    if len(back_play) > 5:
        back_play.pop(5)

    try:
        now_play = next_play[0].copy()
        next_play.pop(0)
    except:
        return

    sql_py("update", [interaction.guild.id, json.dumps(back_play), json.dumps(now_play), json.dumps(next_play)])

    if voice_client.is_connected():
        voice_client.play(
            discord.FFmpegPCMAudio(source=f'https://smashup.ru/stream/mashup/{now_play[0]}.mp3', **FFMPEG_OPTIONS))


class BVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.play_and_stop_play_mashup.start()

    @tasks.loop(seconds=5.0)
    async def play_and_stop_play_mashup(self):
        for i in stop_check_lister:
            if not i[1][0].is_connected():
                try:
                    stop_check_lister.remove(i)
                except:
                    return ()

            if not i[1][0].is_playing():
                if len(i[1][0].channel.members) > 1:
                    if not i[1][0].is_paused():
                        await play_global(i[1][0], i[1][1])
                        i[0] = i[0] + 1
                else:
                    i[0] = i[0] + 1
            else:
                i[0] = 0

            if i[0] == 9:
                sql_py("update_next", [i[1][1].guild.id, json.dumps([])])
                await i[1][0].disconnect()
                try:
                    stop_check_lister.remove(i)
                except:
                    return ()

    @commands.slash_command(name="m-play", description="Добавить мэшапы в очередь")
    @option("search", description="Введите название или автора мэшапа")
    async def _mashup_play(self, interaction, search: str):
        playlist_id = PLAYLIST_LINK_REGEX.get_group(search, 1)
        view = None
        if playlist_id is not None:
            response = requests.get(f"https://smashup.ru/playlist/get?id={playlist_id}", cookies=COOKIES).json()

            mashups = response[0]['mashups']
            emb = classic_embed([discord.Embed(title=f"{response[0]['owner']} - {response[0]['name']}",
                                               description=f"Добавлено {len(response)} "
                                                           f"{get_noun_ending(len(response), ['мэшап', 'мэшапа', 'мэшапов'])}"
                                                           f" в очередь"), [], [], [], []])

            check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))
            if check[0] == "respond":
                emb = classic_embed([discord.Embed(description=check[1]),
                                     [], [], [], []])
            elif check[0] == "voice":
                bad = False

                if check[1] is None:
                    try:
                        voice_client = await interaction.user.voice.channel.connect()
                    except:
                        emb = classic_embed([discord.Embed(description="Боту не хватает прав для подключения к вашему каналу!"),
                                             [], [], [], []])
                        bad = True
                else:
                    voice_client = check[1]

                if not bad:
                    mashup_list = []
                    response1 = requests.get(f"https://smashup.ru/mashup/get?id={','.join(map(str, mashups))}", cookies=COOKIES).json()

                    for i in response1:
                        mashup_list.append([int(i['id']), f"{i['name']} - {i['owner']}", interaction.user.id])
                    emb = classic_embed( [discord.Embed(description="Мэшапы добавлены"),[], [], [], []])

                    await interaction.channel.send(embeds=[
                        discord.Embed(title=f" {interaction.user.display_name} добавляет в очередь",
                                      description=f"Плейлист **{response[0]['name']}** - {response[0]['owner']}")], delete_after=20)
                    await add_to_play(voice_client, interaction, mashup_list)

        else:
            response = requests.get(f"https://smashup.ru/search/mashups?query={search}", cookies=COOKIES).json()

            if not response:
                answer = "Ничего не найдено"
                emb = classic_embed([discord.Embed(description=answer), [], [], [], []])
            else:
                rl = 0
                mlist = []
                mlist_fields = []
                for i in response:
                    if rl > 8:
                        continue
                    else:
                        rl += 1
                        mlist.append(
                            discord.SelectOption(label=f"{i['name']}", description=f"{i['owner']}", value=f"{i['id']}"))
                        mlist_fields.append(discord.EmbedField(name=f"{i['name']}",
                                                               value=f"[{i['owner']}](https://smashup.ru/?profile={i['owner'].replace(' ', '%20')})\n"
                                                                     f"`{i['streams']}💿` `{i['likes']}❤️`",
                                                               inline=True))

                emb = classic_embed([discord.Embed(title=f"ТОП-{rl} поиска",
                                                   description=f" Всего {get_noun_ending(len(response), ['был найден', 'было найдено', 'было найдено'])} "
                                                               f"{len(response)} {get_noun_ending(len(response), ['мэшап', 'мэшапа', 'мэшапов'])}",
                                                   fields=mlist_fields), [], [], [], []])
                selector = Select(
                    custom_id="Choose_mashup",
                    placeholder="Выберите нужный вам мэшап",
                    min_values=1,
                    max_values=len(mlist),
                    options=mlist)
                view = View()
                view.add_item(selector)

        return await interaction.respond(embeds=[emb], view=view, ephemeral=True)

    @commands.slash_command(name="m-pause", description="Поставить проигрывание на паузу")
    async def _mashup_pause(self, interaction):
        check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))

        if check[0] == "respond":
            answer = check[1]
        elif check[0] == "voice":
            if check[1] is None:
                answer = "Бот не находится в вашем канале!"
            else:
                answer = "Проигрывание поставленно на паузу"
                voice_client = check[1]
                voice_client.pause()
        emb = classic_embed([discord.Embed(description=answer), [], [], [], []])

        return await interaction.respond(embeds=[emb], ephemeral=True)

    @commands.slash_command(name="m-info", description="Информация про предыдущие, текущий и следующие мэшапы")
    async def _mashup_info(self, interaction):
        all_get = sql_py("get", [interaction.guild.id])
        back_play = json.loads(all_get['back_play'])
        now_play = json.loads(all_get['now_play'])
        next_play = json.loads(all_get['next_play'])

        if not now_play:
            emb = classic_embed(
                [discord.Embed(
                    title=f"Информация:",
                    description="На этом сервере еще не слушали мэшапы"),
                    [],
                    [],
                    [],
                    []])
            return await interaction.respond(embeds=[emb], ephemeral=True)

        response = requests.get(f"https://smashup.ru/mashup/get?id={now_play[0]}", cookies=COOKIES).json()[0]

        if back_play:
            back_list = ""
            for i in back_play:
                back_list += f"• {i[1]}\n"
        else:
            back_list = "—"

        if next_play:
            next_list = ""
            c_next = 0
            for i in next_play:
                c_next += 1
                next_list += f"• {i[1]}\n"
                if 5 == c_next:
                    break
            if len(next_play) > 5:
                next_list += f"*и еще {len(next_play) - 5}*"
        else:
            next_list = "—"

        ndescription = now_play[1]
        mlist_fields = [
            discord.EmbedField(name=f"Сейчас играет:",
                               value=f"{ndescription}\n`{response['streams']}💿` `{response['likes']}❤️`\n\n"
                                     f"`Включил` {(await self.bot.fetch_user(now_play[2])).mention}",
                               inline=False),
            discord.EmbedField(name=f"Закончились:", value=f"{back_list}", inline=True),
            discord.EmbedField(name=f"Следующие:", value=f"{next_list}", inline=True)
        ]

        emb = classic_embed(
            [discord.Embed(
                title=f"Информация:",
                fields=mlist_fields),
                [],
                [],
                [],
                [f'https://smashup.ru/uploads/mashup/{now_play[0]}_400x400.png']])

        return await interaction.respond(embeds=[emb], ephemeral=True)

    @commands.slash_command(name="m-stop", description="Очистить очередь и выйти")
    async def _mashup_stop(self, interaction):
        check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))

        if check[0] == "respond":
            answer = check[1]
        elif check[0] == "voice":
            if check[1] is None:
                answer = "Бот не находится в вашем голосовом канале"
            else:
                answer = "Проигрывание окончено"
                voice_client = check[1]
                sql_py("update_next", [interaction.guild.id, json.dumps([])])
                for i in stop_check_lister:
                    if i[1][0] == voice_client:
                        try:
                            stop_check_lister.remove(i)
                        except:
                            answer = "Проигрывание окончено"
                await voice_client.disconnect()
                await interaction.channel.send(
                    embeds=[discord.Embed(title=f" {interaction.user.display_name} отключает бота")], delete_after=60)

        emb = classic_embed([discord.Embed(description=answer), [], [], [], []])
        return await interaction.respond(embeds=[emb], ephemeral=True)

    @commands.slash_command(name="m-skip", description="Пропустить текущий мэшап в очереди")
    async def _mashup_skip(self, interaction):
        check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))

        if check[0] == "respond":
            answer = check[1]
        elif check[0] == "voice":
            if check[1] is None:
                answer = "Бот не находится в вашем канале"
            else:
                all_get = sql_py("get", [interaction.guild.id])
                now_play = json.loads(all_get['now_play'])
                if not now_play:
                    answer = "Мэшапы закончились"
                else:
                    answer = "Мэшап пропущен"
                    voice_client = check[1]
                    voice_client.stop()
                    await interaction.channel.send(embeds=[
                        discord.Embed(title=f" {interaction.user.display_name} пропускает мэшап",
                                      description=f"{now_play[1]}\n`Включил` {(await self.bot.fetch_user(now_play[2])).mention}")],
                                                   delete_after=20)

        emb = classic_embed([discord.Embed(description=answer), [], [], [], []])
        return await interaction.respond(embeds=[emb], ephemeral=True)

    @commands.slash_command(name="m-resume", description="Продолжить проигрывание")
    async def _mashup_resume(self, interaction):
        check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))

        if check[0] == "respond":
            answer = check[1]
        elif check[0] == "voice":
            if check[1] is None:
                answer = "Бот не находится в вашем канале"
            else:
                answer = "Проигрывание возобновлено"
                voice_client = check[1]
                voice_client.resume()

        emb = classic_embed([discord.Embed(description=answer), [], [], [], []])
        return await interaction.respond(embeds=[emb], ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        try:
            p = interaction.data['custom_id']
        except:
            return ()

        if p == "Choose_mashup":
            check = voice_check(interaction, discord.utils.get(self.bot.voice_clients, guild=interaction.guild))
            if check[0] == "respond":
                answer = check[1]
            elif check[0] == "voice":
                bad = False

                if check[1] is None:
                    try:
                        voice_client = await interaction.user.voice.channel.connect()
                    except:
                        answer = "Боту не хватает прав для подключения к вашему каналу!"
                        bad = True
                else:
                    voice_client = check[1]

                if not bad:
                    add_list = ""

                    for i in interaction.data['values']:
                        add_list += f"{i},"

                    response = requests.get(f"https://smashup.ru/mashup/get?id={add_list}", cookies=COOKIES).json()

                    add_list = ""
                    mashup_list = []

                    for i in response:
                        add_list += f" **{i['name']}** - {i['owner']} ,"
                        mashup_list.append([int(i['id']), f"{i['name']} - {i['owner']}", interaction.user.id])
                    answer = "Мэшапы добавлены"

                    await interaction.channel.send(embeds=[
                        discord.Embed(title=f" {interaction.user.display_name} добавляет в очередь",
                                      description=f"{add_list[0:len(add_list) - 2]}")], delete_after=20)
                    await add_to_play(voice_client, interaction, mashup_list)

            emb = classic_embed([discord.Embed(description=answer), [], [], [], []])
            return await interaction.response.edit_message(embeds=[emb], view=None)


def setup(bot):
    bot.add_cog(BVoice(bot))
