from discord.ext import commands
import discord
import random

import config


class Mention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        if message.content == 'シート':
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            embed.set_author(
                name='シート',
                icon_url=self.bot.user.avatar_url)
            embed.description = f"[放置狩りシート](https://docs.google.com/spreadsheets/d/1Zt-3rUv3m8fOJJyQAKpyC9qiFopBMXeQGSRYiLvFWjM/edit#gid=0)"
            await message.channel.send(
                f"{message.author.mention} シートのリンクだ…よ",
                embed=embed)


def setup(bot):
    bot.add_cog(Mention(bot))
