from discord.ext import commands
import discord

import re


class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cal(self, ctx, *, arg: str):
        # x を * に変換
        _arg = arg.replace(' ', '')
        formula = re.sub('x', '*', _arg)
        try:
            anser = eval(formula)
        except Exception:
            anser = None

        if anser is not None:
            result = f"計算の結果だ…よ\n```{formula} = {anser}```"
        else:
            result = "式が正しくないよ…もう一度確認してみて…"

        await ctx.channel.send(result)


def setup(bot):
    bot.add_cog(Calculator(bot))
