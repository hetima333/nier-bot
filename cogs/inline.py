import re

from discord.ext import commands
import discord


class Inline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.URL_REG = re.compile(
            r"https://discord.com/channels/(?P<guild_id>\d+)/(?P<channel_id>\d+)/(?P<msg_id>\d+)")

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
            msg_id = int(result.group("msg_id"))
            link_msg = await link_channel.fetch_message(msg_id)
            member = await message.guild.fetch_member(link_msg.author.id)
        except Exception as e:
            print(e)
        else:
            # 引用をつけて投稿
            send_msg = "> " + member.display_name + " さんの投稿\n"
            send_msg += link_msg.clean_content
            await message.channel.send(send_msg)


def setup(bot):
    bot.add_cog(Inline(bot))
