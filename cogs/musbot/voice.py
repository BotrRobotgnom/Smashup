import json
import discord
import asyncio
from discord.ext import commands, tasks
from discord.commands import permissions, option
import requests
from sqlfunc import sql_py
from discord.ui import Button, View, Modal, Select


def voice_chek(Interaction, voice_client):
  if Interaction.user.voice:
    if voice_client:
      if Interaction.user.voice.channel != voice_client.channel:
        return ["respond", "Бот в другом войсе"]
      else:
        return ["voice", voice_client]
    else:
      return ["voice", None]
  else:
    return ["respond","Вы не в войсе"]

def clasic_embed(emb_list):
  #embed, author, fields, image, footer, thumbnail
  emb = emb_list[0]
  if emb_list[1] != []:
    emb.set_author(name = emb_list[1][0], url = emb_list[1][1], icon_url = emb_list[1][2])
  if emb_list[2] != []:
    emb.set_image(emb_list[2][0])
  if emb_list[3] != []:
    emb.set_footer(text = emb_list[3][0], icon_url = emb_list[3][1])
  if emb_list[4] != []:
    emb.set_thumbnail(url=emb_list[4][0])
  return emb

def getNounEnding(number, words):
  if len(words) == 3:
    return words[2 if (number % 100 > 4 and number % 100 < 20) else [2, 0, 1, 1, 1, 2][abs(number) % 10 if (number % 10 < 5) else 5]]

async def add_to_play(voice_client,Interaction,mashup_list):
  all_get = sql_py("get",[Interaction.guild.id])
  new_next = json.loads(all_get['next_play'])
  for i in mashup_list:
    new_next.append(i)
  sql_py("update_next",[Interaction.guild.id,json.dumps(new_next)])
  if not voice_client.is_playing():
    stop_check_lister.append([0, [voice_client,Interaction]])
    
stop_check_lister=[]
  
async def play_global(voice_client,Interaction):
  all_get = sql_py("get",[Interaction.guild.id])
  back_play=json.loads(all_get['back_play'])
  now_play=json.loads(all_get['now_play'])
  next_play=json.loads(all_get['next_play'])
  if next_play == []:
    return
  if now_play != []:
    back_play.insert(0,now_play.copy())
    if len(back_play)>5:
      back_play.pop(5)
    now_play=[]
  try:
    now_play= next_play[0].copy()
    next_play.pop(0)
  except:
    return
  sql_py("update",[Interaction.guild.id,json.dumps(back_play),json.dumps(now_play),json.dumps(next_play)])
  FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
  if voice_client.is_connected():
    voice_client.play(discord.FFmpegPCMAudio(source=f'https://smashup.ru/stream/mashup/{now_play[0]}.mp3', **FFMPEG_OPTIONS))


class BVoice(commands.Cog):
  def __init__(self,bot):
    self.bot = bot
    self.play_and_stop_play_mashup.start()
  #tlanguage: Option(str, "language",autocomplete=discord.utils.basic_autocomplete(tl)), stext: Option(str, "text to voice")

  @tasks.loop(seconds=5.0)
  async def play_and_stop_play_mashup(self):
    for i in stop_check_lister:
      if not i[1][0].is_connected():
        try:
          stop_check_lister.remove(i)
        except:
          return()
      if not i[1][0].is_playing():
        if len(i[1][0].channel.members)>1:
          if not i[1][0].is_paused():
            await play_global(i[1][0],i[1][1])
            i[0] = i[0] + 1
        else:
          i[0] = i[0] + 1
      else:
        i[0] = 0
      if i[0] == 9:
        sql_py("update_next",[i[1][1].guild.id,json.dumps([])])
        await i[1][0].disconnect()
        try:
          stop_check_lister.remove(i)
        except:
          return()
  


  @commands.slash_command(name ="m-play", description="paly mashup")
  @option("search", description="Ведите название/автора мэшапа")
  async def _mashup_paly_voice(self, Interaction, search: str):
    viwe=None
    cookies = {'token': '7f5bc728-1019-4ca0-ac89-de77c2d868f1'}
    response = requests.get(f"https://smashup.ru/search/mashups?query={search}", cookies=cookies).json()
    if response == []:
      answer = "Ничего не найдено"
      emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
    else:
      rl = 0
      mlist = []
      mlist_fields=[]
      for i in response:
        if rl > 8:
          continue
        else:
          rl+=1
          mlist.append(discord.SelectOption(label=f"{i['name']}", description=f"{i['owner']}", value=f"{i['id']}"))
          mlist_fields.append(discord.EmbedField(name=f"{i['name']}", value=f"[{i['owner']}](https://smashup.ru/?profile={i['owner']})\n`{i['streams']}💿` `{i['likes']}❤️`", inline=True))
    
      emb = clasic_embed([discord.Embed(title= f"ТОП-{rl} поиска",description=f" Всего {getNounEnding(len(response),['был найден','было найдено','было найдено'])} {len(response)} {getNounEnding(len(response),['мэшап','мэшапа','мэшапов'])}",fields=mlist_fields),[],[],[],[]])
      selector = Select(
          custom_id="Choose_mashup",
          placeholder="Выберете нужный вам мэшап.",
          min_values = 1,
          max_values = len(mlist),
          options = mlist)
      viwe = View()
      viwe.add_item(selector)
    return await Interaction.respond(embeds=[emb],view=viwe, ephemeral=True)


  @commands.slash_command(name ="m-pause", description="pause mashup")
  async def _mashup_puse(self, Interaction):
    check = voice_chek(Interaction, discord.utils.get(self.bot.voice_clients, guild=Interaction.guild))
    if check[0] == "respond":
      answer = check[1]
    elif check[0] == "voice":
      if check[1] is None:
        answer ="Бот не находится в вашем канале"
      else:
        answer = "Проигрывание поставленно на пауза"
        voice_client=check[1]
        voice_client.pause()
    emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
    return await Interaction.respond(embeds=[emb], ephemeral=True)

  @commands.slash_command(name ="m-info", description="mashup info")
  async def _mashup_info(self, Interaction):
    all_get = sql_py("get",[Interaction.guild.id])
    back_play=json.loads(all_get['back_play'])
    now_play=json.loads(all_get['now_play'])
    next_play=json.loads(all_get['next_play'])

    if now_play == []:
      emb = clasic_embed(
      [discord.Embed(
        title= f"Информация:",
        description="На этом сервере еще не слушали мэшапы"),
        [],
        [],
        [],
        []])
      return await Interaction.respond(embeds=[emb], ephemeral=True)

    cookies = {'token': '7f5bc728-1019-4ca0-ac89-de77c2d868f1'}
    response = requests.get(f"https://smashup.ru/mashup/get?id={now_play[0]}", cookies=cookies).json()[0]

    if back_play !=[]:
      back_list = ""
      for i in back_play:
        back_list += f"•{i[1]}\n"
    else:
      back_list = "Нету информации"
    
    if next_play !=[]:
      next_list = ""
      c_next = 0
      for i in next_play:
        c_next+=1
        next_list += f"•{i[1]}\n"
        if 5 == c_next:
          break
      if len(next_play)>5:
        next_list += f"и еще {len(next_play)-5}"
    else:
      next_list = "Нету информации"

    ndescription = now_play[1]
    mlist_fields=[
      discord.EmbedField(name=f"Сейчас играет:", value=f"{ndescription}\n`{response['streams']}💿` `{response['likes']}❤️`\n\n`Включил` {(await self.bot.fetch_user(now_play[2])).mention}", inline=False),
      discord.EmbedField(name=f"Закончились:", value=f"{back_list}", inline=True),
      discord.EmbedField(name=f"Дальше:", value=f"{next_list}", inline=True)
    ]


    emb = clasic_embed(
      [discord.Embed(
        title= f"Информация:",
        fields=mlist_fields),
        [],
        [],
        [],
        [f'https://smashup.ru/uploads/mashup/{now_play[0]}_400x400.png']])
    return await Interaction.respond(embeds=[emb], ephemeral=True)

  @commands.slash_command(name ="m-stop", description="stop mashup")
  async def _mashup_stop(self, Interaction):
    check = voice_chek(Interaction, discord.utils.get(self.bot.voice_clients, guild=Interaction.guild))
    if check[0] == "respond":
      answer = check[1]
    elif check[0] == "voice":
      if check[1] is None:
        answer ="Бот не находится в вашем канале"
      else:
        answer = "Проигрывание окончено"
        voice_client=check[1]
        sql_py("update_next",[Interaction.guild.id,json.dumps([])])
        for i in stop_check_lister:
          if i[1][0]==voice_client:
            try:
              stop_check_lister.remove(i)
            except:
              answer = "Проигрывание окончено"
        await voice_client.disconnect()
        await Interaction.channel.send(embeds=[discord.Embed(title= f" {Interaction.user.display_name} отключает бота")],delete_after=60)
    emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
    return await Interaction.respond(embeds=[emb], ephemeral=True)
  
  @commands.slash_command(name ="m-skip", description="skip mashup")
  async def _mashup_skip(self, Interaction):
    check = voice_chek(Interaction, discord.utils.get(self.bot.voice_clients, guild=Interaction.guild))
    if check[0] == "respond":
      answer = check[1]
    elif check[0] == "voice":
      if check[1] is None:
        answer ="Бот не находится в вашем канале"
      else:
        all_get = sql_py("get",[Interaction.guild.id])
        now_play=json.loads(all_get['now_play'])
        if now_play==[]:
          answer = "Мэшапы закончились"
        else:
          answer = "Мэшап пропущен"
          voice_client=check[1]
          voice_client.stop()
          await Interaction.channel.send(embeds=[discord.Embed(title= f" {Interaction.user.display_name} пропускает мэшап",description=f"{now_play[1]}\n`Включил` {(await self.bot.fetch_user(now_play[2])).mention}")],delete_after=20)
    emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
    return await Interaction.respond(embeds=[emb], ephemeral=True)

  @commands.slash_command(name ="m-resume", description="resume mashup")
  async def _mashup_resume(self, Interaction):
    check = voice_chek(Interaction, discord.utils.get(self.bot.voice_clients, guild=Interaction.guild))
    if check[0] == "respond":
      answer = check[1]
    elif check[0] == "voice":
      if check[1] is None:
        answer ="Бот не находится в вашем канале"
      else:
        answer = "Проигрывание возобновлено"
        voice_client=check[1]
        voice_client.resume()
    emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
    return await Interaction.respond(embeds=[emb], ephemeral=True)

  @commands.Cog.listener()
  async def on_interaction(self,Interaction):
    try:
      p = Interaction.data['custom_id']
    except:
      return()
    if p == "Choose_mashup":
      check = voice_chek(Interaction, discord.utils.get(self.bot.voice_clients, guild=Interaction.guild))
      if check[0] == "respond":
        answer = check[1]
      elif check[0] == "voice":
        if check[1] is None:
          try:
            voice_client = await Interaction.user.voice.channel.connect()
          except:
            answer ="Бот не может подключится к вашему каналу"
        else:
          voice_client = check[1]
        add_list = ""
        for i in Interaction.data['values']:
          add_list += f"{i},"
        cookies = {'token': '7f5bc728-1019-4ca0-ac89-de77c2d868f1'}
        response = requests.get(f"https://smashup.ru/mashup/get?id={add_list}", cookies=cookies).json()

        add_list = ""
        mashup_list = []
        for i in response:
          add_list += f" **{i['name']}** - {i['owner']} ,"
          mashup_list.append([int(i['id']),f"{i['name']}-{i['owner']}",Interaction.user.id])
        answer="Мэшапы добавлены"
        await Interaction.channel.send(embeds=[discord.Embed(title= f" {Interaction.user.display_name} добавляет в очередь",description=f"{add_list[0:len(add_list)-2]}")],delete_after=20)
        await add_to_play(voice_client,Interaction,mashup_list)

      emb = clasic_embed([discord.Embed(description=answer),[],[],[],[]])
      return await Interaction.response.edit_message(embeds=[emb],view=None)



      



def setup(bot):
  bot.add_cog(BVoice(bot))