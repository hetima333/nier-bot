import random
import re

import discord
from discord.ext import commands


class DiceRoll(commands.Cog, name='ダイス'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(usage='1d6 など', aliases=["r"])
    async def roll(self, ctx, *, arg: str = '1d100'):
        '''
        ダイスロールを行なうわ
        例えば、6面ダイスを1回振りたい時は -r 1d6 になるわ
        -r とだけすると、1d100を振るわ
        '''
        await self._send_dice_roll_result(ctx, arg)

    async def _send_dice_roll_result(self, ctx, arg: str = '1d100'):
        dice_reg = r'(?P<num>\d{1,})d(?P<face>\d{1,})'
        reg_result = re.search(dice_reg, arg)

        # xdy形式ではないときは警告を返信する
        if reg_result is None:
            await ctx.channel.send(f'{ctx.author.mention}\n\
                指定方法が間違っている…よ\n例えば、6面ダイスを1回振りたい時は`!!r 1d6`になる…よ')
            return

        num = int(reg_result.group('num'))
        face = int(reg_result.group('face'))
        mes = f'```\n{num}d{face} = '
        result = 0
        for item in self._roll_dice(face, num):
            mes += f'{item} + '
            result += item
        # 最後に末尾の' + 'を削除する
        mes = mes[:-3]
        mes += f' = {result}\n```'
        # 連投されたときに誰のダイスロールかわからなくなるので、メンションをつける
        await ctx.channel.send(f'{ctx.author.mention}\n{mes}')

    def _roll_dice(self, face, num):
        results = []
        for i in range(num):
            dice = random.randint(1, face)
            results.append(dice)

        return results


def setup(bot):
    bot.add_cog(DiceRoll(bot))
