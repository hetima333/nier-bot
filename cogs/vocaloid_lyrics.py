import aiohttp
import discord
import json
import urllib

from discord.ext import commands

from config import Config


class VocaloidLyrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['vly'])
    async def vocaloid_lyrics(self, ctx, *, message: str):
        url = 'https://vocadb.net/api/songs'
        url += f"?query={urllib.parse.quote(message)}"
        url += "&songTypes=Original"
        url += "&nameMatchMode=Auto"
        url += "&fields=Lyrics"

        await ctx.channel.trigger_typing()

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                v = json.loads(await r.read())

        try:
            items = v['items'][0]
            artist = items['artistString']
            song = items['defaultName']
            lyrics = items['lyrics'][0]['value']
        except IndexError:
            await ctx.channel.send("ごめんなさい…歌詞を見つけられなくて…")
        else:
            embed = discord.Embed(color=0x8080c0)
            embed.title = song
            embed.description = f"{artist}\n\n{lyrics}"
            await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(VocaloidLyrics(bot))
