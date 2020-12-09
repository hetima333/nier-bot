import re

from discord.ext import commands
import discord


class Inline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_REG = re.compile(
            r"https://discord.com/channels/(?P<guild_id>\d+)/(?P<channel_id>\d+)/(?P<message_id>\d+)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # DMは無視
        if message.guild is None:
            return

        result = self.URL_REG.search(message.clean_content)
        if result is None:
            return

        # 同じサーバー内のメッセージ以外は無視
        guild_id = int(result.group("guild_id"))
        if guild_id != message.guild.id:
            return

        # メッセージをフェッチする
        try:
            channel_id = int(result.group("channel_id"))
            link_channel = await self.bot.fetch_channel(channel_id)
            message_id = int(result.group("message_id"))
            link_message = await link_channel.fetch_message(message_id)
        except Exception as e:
            print(e)
        else:
            # 引用をつけて投稿
            await message.channel.send("> " + link_message.clean_content)


def setup(bot):
    bot.add_cog(Inline(bot))
