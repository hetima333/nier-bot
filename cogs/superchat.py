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
        self.path = Path("../lunalu-bot/data")

    def _get_money_colors(self, value: int) -> list:
        with (self.path / "json/superchat/colors.json").open() as f:
            color_data = json.load(f)

        # 色分岐
        if value < 500:
            colors = color_data.get("200")
        elif value < 1000:
            colors = color_data.get("500")
        elif value < 2000:
            colors = color_data.get("1000")
        elif value < 5000:
            colors = color_data.get("2000")
        elif value < 10000:
            colors = color_data.get("5000")
        else:
            colors = color_data.get("10000")

        return colors

    def _get_random_money(self) -> int:
        with (self.path / "json/superchat/values.json").open() as f:
            values_data = json.load(f)

        # 金額のランダム生成
        weights = [float(v) for v in values_data.keys()]
        money = int(random.choice(random.choices(
            list(values_data.values()), weights=weights)[0]))

        return money

    def _format_text(self, max_count: int, text: str):
        # スタンプを正規表現で見つけて配列に格納してメタ文字に置換する
        stamp_re = re.compile(r"<:\w+:(\d+)>")
        # MEMO: &@をダミー文字としているので、@@が含まれた文章が投稿されたらずれる
        m = re.sub(stamp_re, '&@', text)

        format_msg = ""
        str_count = 0
        emoji_list = []

        # 1行36文字に収める
        for i, s in enumerate(m):
            if unicodedata.east_asian_width(s) in 'FWA':
                str_count += 2
            else:
                str_count += 1

            # 絵文字は&%に置き換える
            if s in emoji.UNICODE_EMOJI:
                emoji_list.append(s)
                format_msg += '&%'
            else:
                format_msg += s

            if s == '\n':
                str_count = 0
            if str_count > max_count:
                format_msg += '\n'
                str_count = 0

        format_msg = re.sub('&\n@', '&@', format_msg)
        if format_msg[-1] == "\n":
            format_msg = format_msg[:-1]
        return format_msg, emoji_list

    async def _get_custom_stamp_list(self, guild: discord.Guild, text: str) -> list:
        # スタンプを正規表現で見つけて配列に格納してメタ文字に置換する
        stamp_re = re.compile(r"<:\w+:(\d+)>")
        # スタンプ合成
        stamp_list = []
        if guild is not None:
            for s in re.findall(stamp_re, text):
                stamp = await guild.fetch_emoji(int(s))
                stamp_list.append(stamp.url)

        return stamp_list

    @commands.command()
    async def sc(self, ctx):
        user = ctx.message.author
        msg = ctx.message.clean_content[4:]

        await ctx.message.delete()

        # 金額のランダム生成
        money = self._get_random_money()
        # 金額に対応した色
        colors = self._get_money_colors(money)

        # 矩形を作成して表示
        main_color = colors['main_color']
        back_color = colors['back_color']
        name_color = colors['name_color']
        text_color = colors['text_color']

        format_msg, emoji_list = self._format_text(36, msg)
        stamp_list = await self._get_custom_stamp_list(ctx.guild, msg)

        lines = format_msg.count(os.linesep)
        text_height = 22
        font_size = 20
        height = 150 + lines * text_height

        im = Image.new("RGBA", (450, height), tuple(main_color))
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 100, 450, height), fill=tuple(back_color))

        # 文字合成
        name_font = ImageFont.truetype(str(self.path / "font/migu-1m-regular.ttf"), font_size)
        # ユーザー名のみ少し薄い色
        draw.multiline_text(
            (110, 20), user.display_name, fill=tuple(name_color), font=name_font)
        del name_font

        text_font = ImageFont.truetype(str(self.path / "font/migu-1m-bold.ttf"), font_size)
        draw.multiline_text(
            (110, 50), f"¥ {'{:,}'.format(money)}", fill=tuple(text_color), font=text_font)

        draw.multiline_text(
            (20, 115), format_msg, fill=tuple(text_color), font=text_font
        )

        offset = [0, 0]
        prev_str = ''
        for i, s in enumerate(format_msg):
            if unicodedata.east_asian_width(s) in 'FWA':
                offset[0] += font_size
            else:
                offset[0] += int(font_size / 2)

            # カスタム絵文字と絵文字を画像に置換
            if s in ['@', '%'] and prev_str == '&':
                pos = [
                    20 + offset[0] - font_size,
                    115 + offset[1]
                ]
                # ダミー文字を塗りつぶし
                draw.rectangle((pos[0], pos[1], pos[0] + font_size,
                                pos[1] + font_size), fill=tuple(back_color))
                # カスタム絵文字の場合
                if s == '@':
                    data = io.BytesIO(await stamp_list.pop(0).read())
                    stamp_img = Image.open(data).convert(
                        'RGBA').resize((20, 20), Image.BICUBIC)
                    im.paste(stamp_img, (pos[0], pos[1]), stamp_img.split()[3])
                # 絵文字の場合
                elif s == '%':
                    if len(emoji_list) > 0:
                        emoji_str = emoji.demojize(emoji_list.pop(0))[1:-1]
                        # 変換されない絵文字が存在するので念の為チェック（2020/10/4時点で⛩のみ）
                        emoji_img_path = self.path / f'img/emoji/{emoji_str}.png'
                        if os.path.isfile(emoji_img_path):
                            emoji_img = Image.open(emoji_img_path).convert('RGBA')
                            im.paste(emoji_img, (pos[0], pos[1]), emoji_img.split()[3])

            prev_str = s

            if s == '\n':
                offset[0] = 0
                offset[1] += text_height

        # ユーザーのサムネを取得してImageに変換
        data = io.BytesIO(await user.avatar_url.read())
        thum = Image.open(data).convert('RGBA')
        del data
        thum = thum.resize((60, 60), Image.BICUBIC)
        # 画像合成
        mask = Image.open(self.path / "img/superchat/mask_circle.jpg").convert('L')
        im.paste(thum, (25, 20), mask.resize((60, 60), Image.HAMMING))

        im.save(self.path / "img/superchat/superchat.png")
        del im

        await ctx.send(file=discord.File(self.path / "img/superchat/superchat.png"))


def setup(bot):
    bot.add_cog(SuperChat(bot))
