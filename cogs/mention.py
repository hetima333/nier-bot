from discord.ext import commands
import discord
import datetime
import random

import config


class Mention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
        embed.description = "[ニーアbotの説明書](https://www.notion.so/hetima333/bot-6bd0bf832f6a4e9ab5984ec6a6ecd805)"
        embed.set_author(
            name='説明書',
            icon_url=self.bot.user.avatar_url)
        await ctx.message.reply("私の説明書だ…よ", embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            serifs = [
                '私はニーア。お願い、私を愛して……私を認めて',
                '私、何でもするから……！　だから……お願い……！　私を愛して……私を認めて！',
                'どうしたら……私を見てくれるの？　どうしたら……私を愛してくれる……の？',
                '大丈夫。あなたを傷つける者、私とデスが全部、消す……から'
            ]

            await message.channel.send(
                f"{message.author.mention} {random.choice(serifs)}")

        # 「滅びろ祇園の風」に反応して画像を送信する
        if "滅びろ祇園の風" == message.content:
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            embed.set_image(
                url='https://cdn.discordapp.com/attachments/467646451170803733/647092862361796616/EG2DHAxUEAETGDe.png')
            embed.set_footer(text=message.author.display_name,
                             icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)

        # 「行け」に反応して画像を送信する
        if "おい" == message.content:
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            urls = [
                'https://cdn.discordapp.com/attachments/500215831784062977/682619031647289428/2020-01-31_23.png',
                'https://cdn.discordapp.com/attachments/500215831784062977/682889819361378305/39909d9e9d631ee2c980c56577d20e3e-png.png',
                'https://cdn.discordapp.com/attachments/683536765977624590/734054219178311740/333fc592439f2795bee1906e3d1b90e9.png'
            ]
            embed.set_image(url=random.choice(urls))
            await message.reply(embed=embed)

        if "はよいけ" == message.content:
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            urls = [
                'https://cdn.discordapp.com/attachments/500215831784062977/685147145560391775/unknown.png',
                'https://cdn.discordapp.com/attachments/500215831784062977/686769829029347356/unknown.png'
            ]
            embed.set_image(url=random.choice(urls))
            await message.channel.send(embed=embed)

        if message.content == 'シート':
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            embed.set_author(
                name='シート',
                icon_url=self.bot.user.avatar_url)
            embed.description = f"[放置狩りシート](https://docs.google.com/spreadsheets/d/1Zt-3rUv3m8fOJJyQAKpyC9qiFopBMXeQGSRYiLvFWjM/edit#gid=0)"
            await message.channel.send(
                f"{message.author.mention} シートのリンクだ…よ",
                embed=embed)

        if message.content in ['はらかみ', 'げんしん', '原神']:
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            embed.set_author(
                name='シート',
                icon_url=self.bot.user.avatar_url)
            embed.description = f"[難民キャンプはらかみ部シート](https://docs.google.com/spreadsheets/d/12ynFBXEb4yTGWI-jI8V097OowdV_cmDQJFh7U-_7gK0/edit?usp=sharing)"
            await message.channel.send(
                f"{message.author.mention} シートのリンクだ…よ",
                embed=embed)


def setup(bot):
    bot.add_cog(Mention(bot))
