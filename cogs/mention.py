from discord.ext import commands
import discord
import random


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

            message.channel.send(
                f"{message.author.mention} {random.choice(serifs)}")


def setup(bot):
    bot.add_cog(Mention(bot))
