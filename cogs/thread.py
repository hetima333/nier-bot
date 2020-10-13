from discord.ext import commands
import discord

import config


class Thread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trigger_emoji = '⏬'
        self.notify_channel_id = 765164881220993034

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = str(payload.emoji)
        # スレッド開始絵文字以外は無視
        if emoji != self.trigger_emoji:
            return

        user = await self.bot.fetch_user(payload.user_id)
        # 絵文字をつけたユーザーがbotだった場合は無視
        if user.bot:
            return

        channel = await self.bot.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        # スレッド開始絵文字が既についていたら処理しない
        if len([str(r.emoji) for r in message.reactions if r.count > 1]) > 0:
            return

        # スレッド開始絵文字をつける
        await message.add_reaction(self.trigger_emoji)

        notify_channel = await self.bot.fetch_channel(self.notify_channel_id)
        category = notify_channel.category
        thread_channel = await category.create_text_channel(f'{message.clean_content[:20]}…のスレッド')

        # 作成日順にソートする。新着通知チャンネルはソートしない
        channels = category.text_channels
        channels.pop(0)
        channels = sorted(channels, reverse=True, key=lambda c: c.created_at)
        for index, ch in enumerate(channels):
            # editだと動作が遅かったので直接加算して、1度だけeditを走らせてソートを適用している
            ch.position = index + 1
            # await ch.edit(position=index + 1)
        await notify_channel.edit(position=0)

        embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
        embed.set_author(name=f"{message.author.display_name}の発言",
                         icon_url=message.author.avatar_url)
        embed.description = f"[スレッド元]({message.jump_url})"

        await channel.send(f"スレッドを開始した…よ <#{thread_channel.id}>")
        await thread_channel.send(f"{message.author.mention} スレッドが開始された…よ", embed=embed)
        await thread_channel.send(f"```{message.clean_content}```")
        await notify_channel.send(f"新しいスレッドが開始された…よ <#{thread_channel.id}>")


def setup(bot):
    bot.add_cog(Thread(bot))
