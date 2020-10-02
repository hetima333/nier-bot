from discord.ext import commands
import discord
import aiohttp
import io
import json
import unicodedata
import random
import os
import re
import emoji

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


class SuperChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color_file = Path("data/json/superchat_data.json")

    @commands.command()
    async def sc(self, ctx, message: str):
        user = ctx.message.author
        name = user.display_name
        msg = ctx.message.clean_content[4:]

        await ctx.message.delete()

        with self.color_file.open() as f:
            d = json.load(f)
            color_data = d["colors"]
            values_data = d["values"]

        # 金額のランダム生成
        weights = [float(v) for v in values_data.keys()]
        money = int(random.choice(random.choices(
            list(values_data.values()), weights=weights)[0]))

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

        # MEMO: 1行38文字(小文字)
        format_msg = ""
        max_count = 36
        str_count = 0

        # スタンプを正規表現で見つけて配列に格納してメタ文字に置換する
        stamp_re = re.compile(r"<:\w+:(\d+)>")
        # MEMO: @@をダミー文字としているので、@@が含まれた文章が投稿されたらずれる
        m, stamp_count = re.subn(stamp_re, '@@', msg)

        # スタンプ合成
        stamp_list = []
        guild = ctx.guild
        if guild is not None:
            for s in re.findall(stamp_re, msg):
                stamp = await guild.fetch_emoji(int(s))
                stamp_list.append(stamp.url)

        # 1行36文字に収める
        for i, s in enumerate(m):
            if unicodedata.east_asian_width(s) in 'FWA':
                str_count += 2
            else:
                str_count += 1

            format_msg += s

            if s == '\n':
                str_count = 0
            if str_count > max_count:
                format_msg += '\n'
                str_count = 0

        format_msg = re.sub('@\n@', '@@', format_msg)

        lines = format_msg.count(os.linesep)
        height = 150 + lines * 22

        im = Image.new("RGBA", (450, height), tuple(main_color))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 100, 450, height), fill=tuple(back_color))

        # 文字合成
        name_font = ImageFont.truetype('data/font/migu-1m-regular.ttf', 20)
        text_font = ImageFont.truetype('data/font/migu-1m-bold.ttf', 20)
        emoji_font = ImageFont.truetype(
            'data/font/TwitterColorEmoji-SVGinOT-OSX.ttf', 20)

        # ユーザー名のみ少し薄い色
        draw.multiline_text(
            (110, 20), name, fill=tuple(name_color), font=name_font)
        draw.multiline_text(
            (110, 50), f"¥ {'{:,}'.format(money)}", fill=tuple(text_color), font=text_font)

        offset = [0, 0]
        prev_str = ''
        for i, s in enumerate(format_msg):
            if s in emoji.UNICODE_EMOJI:
                draw.text((20 + offset[0], 115 + offset[1]),
                          s, fill=tuple(text_color), font=emoji_font)
                offset[0] += 20
            elif unicodedata.east_asian_width(s) in 'FWA':
                draw.text((20 + offset[0], 115 + offset[1]),
                          s, fill=tuple(text_color), font=text_font)
                offset[0] += 22
            else:
                draw.text((20 + offset[0], 115 + offset[1]),
                          s, fill=tuple(text_color), font=text_font)
                offset[0] += 11

            if s == '@' and prev_str == '@':
                pos = [20 + offset[0] - 22, 115 + offset[1]]
                draw.rectangle((pos[0], pos[1], pos[0] + 50, pos[1] + 25), fill=tuple(back_color))
                data = io.BytesIO(await stamp_list.pop(0).read())
                stamp_img = Image.open(data).convert('RGBA')
                stamp_img = stamp_img.resize((20, 20), Image.BICUBIC)
                im.paste(stamp_img, (pos[0], pos[1]), stamp_img.split()[3])
            prev_str = s

            if s == '\n':
                offset[0] = 0
                offset[1] += 22

        # 画像合成
        thum = thum.resize((60, 60), Image.BICUBIC)
        mask = Image.open('data/img/mask_circle.jpg').convert('L')
        im.paste(thum, (25, 20), mask.resize((60, 60), Image.HAMMING))

        im.save('data/img/superchat.png')

        await ctx.send(file=discord.File('data/img/superchat.png'))


def setup(bot):
    bot.add_cog(SuperChat(bot))
