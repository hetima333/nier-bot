from discord.ext import commands
import discord
import aiohttp
import io
import json
import unicodedata
import random
import os
import re

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class SuperChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color_file = Path("data/json/superchat_color.json")

    @commands.command()
    async def sc(self, ctx, message: str):
        user = ctx.message.author
        name = user.display_name
        values = [200, 500, 1000, 2000, 5000, 10000]
        money = random.choice(values)
        # msg = message
        msg = ctx.message.clean_content[4:]

        await ctx.message.delete()

        with self.color_file.open() as f:
            color_data = json.load(f)

        # 色分岐
        if money < 500:
            colors = color_data.get("200")
        elif money < 1000:
            colors = color_data.get("500")
        elif money < 2000:
            colors = color_data.get("1000")
        elif money < 5000:
            colors = color_data.get("2000")
        elif money < 10000:
            colors = color_data.get("5000")
        else:
            colors = color_data.get("10000")

        # ユーザーのサムネを取得してImageに変換
        data = io.BytesIO(await user.avatar_url.read())
        thum = Image.open(data).convert('RGBA')

        # 矩形を作成して表示
        main_color = colors['main_color']
        back_color = colors['back_color']
        name_color = colors['name_color']
        text_color = colors['text_color']

        # MEMO: 1行40文字(小文字)
        format_msg = ""
        for v in msg.splitlines():
            if len(v) > 20:
                format_msg += '\n'.join([v[i: i+20]
                                         for i in range(0, len(v), 20)])
            else:
                format_msg += v + '\n'
        # 改行を削除
        format_msg = format_msg[:-1]

        lines = format_msg.count(os.linesep)
        height = 150 + lines * 22

        im = Image.new("RGBA", (450, height), tuple(main_color))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 100, 450, height), fill=tuple(back_color))

        # 文字合成
        name_font = ImageFont.truetype('data/font/migu-1m-regular.ttf', 20)
        text_font = ImageFont.truetype('data/font/migu-1m-bold.ttf', 20)

        # ユーザー名のみ少し薄い色
        draw.multiline_text(
            (110, 20), name, fill=tuple(name_color), font=name_font)
        draw.multiline_text(
            (110, 50), f"¥ {'{:,}'.format(money)}", fill=tuple(text_color), font=text_font)
        draw.multiline_text(
            (25, 115), format_msg, fill=tuple(text_color), font=text_font)

        # 画像合成
        thum = thum.resize((60, 60))
        mask = Image.open('data/img/mask_circle.jpg').convert('L')
        im.paste(thum, (25, 20), mask.resize((60, 60)))

        im.save('data/img/superchat.png')

        await ctx.send(file=discord.File('data/img/superchat.png'))


def setup(bot):
    bot.add_cog(SuperChat(bot))
