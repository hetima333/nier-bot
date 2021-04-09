import json
import re
from pathlib import Path

from discord.ext import commands
import discord

import config


class AmongUs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MAP_DATA_FILE = Path('data/json/amongus.json')

    @commands.command()
    async def au(self, ctx, map_name: str):
        with self.MAP_DATA_FILE.open() as f:
            map_data = json.loads(f.read())

        for v in map_data:
            r = re.fullmatch(f"{v['reg']}", map_name, re.I)

            if r is not None:
                embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
                embed.set_image(url=v['img_url'])
                await ctx.message.reply(
                    f"{v['formal_name']}のマップだ…よ", embed=embed)

                return

        await ctx.message.reply(f"{map_name} という名前のマップが見つからないわ…ごめんなさい")


def setup(bot):
    bot.add_cog(AmongUs(bot))
