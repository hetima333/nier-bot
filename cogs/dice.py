import random
import re

import discord
from discord.ext import commands


class DiceRoll(commands.Cog, name='ダイス'):
    def __init__(self, bot):
        self.bot = bot
        # NOTE: 一旦加減算のみ
        self.dice_re = re.compile(r'(?P<symbol>\+|\-)?((?P<num>\d{1,2})?d(?P<face>\d{1,3}))?(?P<value>\d{1,3})?')

    @commands.command(usage='1d6 など', aliases=["r"])
    async def roll(self, ctx, *, arg: str = '1d100'):
        '''
        ダイスロールを行なうわ
        例えば、6面ダイスを1回振りたい時は -r 1d6 になるわ
        -r とだけすると、1d100を振るわ
        '''
        # await self._send_dice_roll_result(ctx, arg)
        await self.send_dice_roll(ctx, arg)

    def get_dice_result(self, src):
        itr = self.dice_re.finditer(src)
        result = {
            "value": 0,
            "text": ""
        }
        for r in itr:
            symbol = r.group('symbol')
            # NOTE: 演算子がなければ+とする
            if symbol is None:
                symbol = '+'

            # 修正値でなければダイスロールを行う
            if r.group('value') is None:
                if r.group('face') is None:
                    continue
                num = 1
                face = r.group('face')
                # d6などの回数指定なしのダイスは1回にする
                if r.group('num') is not None:
                    num = int(r.group('num'))
                roll = self.roll_dice(face, num)
                text = symbol
                text += "+".join([str(v) for v in roll])
            else:
                text = f"{symbol}{r.group('value')}"

            # 末尾に空白を入れておく
            result["text"] += f"{text}"
            result["value"] = eval(f"{result['value']}{text}")

        # 最初の+だけ削除
        if result["text"].startswith('+'):
            result["text"] = result["text"].lstrip('+')

        # if result["text"] == "":
        #     return None

        return result

    async def send_dice_roll(self, ctx, arg: str = '1d100'):
        result = self.get_dice_result(arg)
        msg = f"{ctx.author.mention} ダイスロールの結果だ…よ\n"
        msg += f"```{arg.strip()} = {result['text']} = {result['value']}```"
        await ctx.channel.send(msg)

    def roll_dice(self, face, num):
        results = []
        for i in range(num):
            dice = random.randint(1, int(face))
            results.append(dice)

        return results


def setup(bot):
    bot.add_cog(DiceRoll(bot))
