from discord.ext import commands
import discord
import requests
from bs4 import BeautifulSoup
import re
import aiohttp
import pandas as pd
import jaconv


class PokemonIndex(commands.Cog, name='ポケモン図鑑'):
    def __init__(self, bot):
        self.bot = bot
        self.MAX_RESULT_NUM = 8

    @commands.command(usage="ポケモンの名前", aliases=['pd'])
    async def pokedex(self, ctx, *args: str):
        '''
        入力されたポケモンの情報を表示するわ
        '''
        df = pd.read_csv('../lunalu-bot/data/csv/pokemon_data.csv')

        # ポケモンの名前が入力されていなかったらエラーを返す
        if len(args) == 0:
            await ctx.send(f'{ctx.author.mention} ポケモンの名前が入力されていないわ…')
            return

        name = jaconv.hira2kata(args[0])
        # 完全一致検索を行なう
        data = df[df['Name'] == name].values
        # 完全一致したポケモンがいなければnameが含まれるポケモンを探す
        if len(data) == 0:
            # フォームで絞り込み検索する
            if len(args) > 1:
                form_name = jaconv.hira2kata(args[1])
                data = df[df['Name'].str.contains(name)]
                data = data[data['Form'].str.contains(
                    form_name, na=False)].values
            else:
                data = df[df['Name'].str.contains(name)].values
        pokemon_list = list()

        if len(data) == 0:
            await ctx.send(f'{ctx.author.mention} ポケモンが見つからなかったわ…')
            return

        for item in data:
            pokemon = {}
            pokemon = {
                "number": str(item[0]).zfill(3),
                "name": item[1],
                "full_name": item[1],
                "form_name": str(item[2]),
                "form_suffix": str(item[3]),
                "type": [
                    str(item[4]),
                    str(item[5])
                ],
                "ability": [
                    str(item[6]),
                    str(item[7]),
                    str(item[8])
                ],
                "stats": [
                    int(item[9]),
                    int(item[10]),
                    int(item[11]),
                    int(item[12]),
                    int(item[13]),
                    int(item[14]),
                ],
                "weight": str(item[15]),
            }
            # フォームがあれば名前に追加する
            if pokemon["form_name"] != 'nan':
                pokemon["full_name"] += f'（{pokemon["form_name"]}）'

            pokemon_list.append(pokemon)

        await ctx.send(
            f'{ctx.author.mention} ポケモンが見つかったわ！',
            embed=await self.create_embed(pokemon_list[0]))

        loopCount = min(self.MAX_RESULT_NUM, len(pokemon_list))-1
        for i in range(loopCount):
            embed = await self.create_embed(pokemon_list[i+1])
            await ctx.send(embed=embed)

    async def create_embed(self, pokemon):
        number = pokemon["number"]
        type_ = pokemon["type"]
        ability = pokemon["ability"]
        stats = pokemon["stats"]
        weight = pokemon["weight"]
        form_suffix = pokemon["form_suffix"]

        poketetsu_link = 'https://yakkun.com/swsh/zukan/n'
        poketetsu_link += number
        icon_link = 'https://www.serebii.net/pokedex-swsh/icon/'
        icon_link += number
        img_link = 'https://www.serebii.net/swordshield/pokemon/'
        img_link += number
        if form_suffix != 'nan':
            poketetsu_link += form_suffix
            icon_link += f'-{form_suffix}'
            img_link += f'-{form_suffix}'
        icon_link += '.png'
        img_link += '.png'

        embed = discord.Embed(color=0x8080c0)
        embed.set_author(
            name=pokemon["name"], url=poketetsu_link, icon_url=icon_link)
        embed.set_thumbnail(url=img_link)

        # タイプの追加
        type_txt = type_[0]
        if type_[1] != 'nan':
            type_txt += f", {type_[1]}"
        # 特性の追加
        ability_txt = ability[0]
        if ability[1] != 'nan':
            ability_txt += f", {ability[1]}"
        if ability[2] != 'nan':
            ability_txt += f", *{ability[2]}"
        # 種族値の追加
        stats_txt = f"{stats[0]}"
        for i in range(5):
            stats_txt += f"-{stats[i+1]}"
        # 重さの追加
        weight_txt = f"{weight}kg"

        # TODO: 対戦考察wikiから情報を持ってきた型や技を追加する

        link = await self.get_serebii_link(number, pokemon["name"])

        embed.add_field(name="図鑑No.", value=number)
        embed.add_field(name="タイプ", value=type_txt)
        embed.add_field(name="特性", value=ability_txt, inline=False)
        embed.add_field(name="種族値", value=stats_txt, inline=False)
        if weight != 'nan':
            embed.add_field(name="重さ", value=weight_txt, inline=False)
        if link is not None:
            embed.add_field(name="リンク", value=link, inline=False)

        return embed

    async def get_serebii_link(self, number, ja_name):
        en_name = ''
        ja_wiki = f'https://wiki.xn--rckteqa2e.com/wiki/{ja_name}'
        # 英名の取得
        # TODO: データセットに英名を追加する
        async with aiohttp.ClientSession() as session:
            async with session.get(ja_wiki) as r:
                if r.status == 200:
                    html = await r.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    td = soup.find("td", attrs={"lang": "en"}).text.strip()
                    en_name = td.strip().lower()

        # 英名が取得できなかったらNoneを返す
        if en_name == '':
            return None

        # 8世代リンクの有無確認
        serebii_link = f'https://www.serebii.net/pokedex-swsh/{en_name}'
        async with aiohttp.ClientSession() as session:
            async with session.get(serebii_link) as r:
                if r.status == 200:
                    return serebii_link

        # 7世代リンクの貼り付け
        return f'https://www.serebii.net/pokedex-sm/{number}.shtml'


def setup(bot):
    bot.add_cog(PokemonIndex(bot))
