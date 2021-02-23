from discord.ext import commands
import discord

import config


class AmongUs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.map_data = {
            'theskeld': {
                'img_url': 'https://cdn.discordapp.com/attachments/500215831784062977/813701787503820820/El3tBPkU8AA8iQE.png',
                'formal_name': 'The Skeld'
            },
            'mirahq': {
                'img_url': 'https://cdn.discordapp.com/attachments/500215831784062977/813701836803670016/El3qJKJU4AUHPDP.png',
                'formal_name': 'MIRA HQ'
            },
            'polus': {
                'img_url': 'https://cdn.discordapp.com/attachments/500215831784062977/813701880454053928/El3qJJkVMAATYAb.png',
                'formal_name': 'Polus'
            }
        }

    @commands.command()
    async def au(self, ctx, map_name: str):
        _map_name = map_name.lower()
        _map_name = _map_name.replace(' ', '')
        map_data = self.map_data.get(_map_name)
        if map_data is None:
            await ctx.message.reply(f"{map_name} という名前のマップが見つからないわ…ごめんなさい")
        embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
        embed.set_image(url=map_data['img_url'])
        await ctx.message.reply(
            f"{map_data['formal_name']}のマップだ…よ", embed=embed)


def setup(bot):
    bot.add_cog(AmongUs(bot))
