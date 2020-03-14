from discord.ext import commands
import discord
import datetime
import random

import config


class Mention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            serifs = [
                '私はニーア。お願い、私を愛して……私を認めて',
                '私、何でもするから……！　だから……お願い……！　私を愛して……私を認めて！',
                'どうしたら……私を見てくれるの？　どうしたら……私を愛してくれる……の？',
                '大丈夫。あなたを傷つける者、私とデスが全部、消す……から'
            ]

            await message.channel.send(
                f"{message.author.mention} {random.choice(serifs)}")

        if message.content == 'シート':
            embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
            embed.set_author(
                name='シート',
                icon_url=self.bot.user.avatar_url)
            embed.description = f"[放置狩りシート](https://docs.google.com/spreadsheets/d/1Zt-3rUv3m8fOJJyQAKpyC9qiFopBMXeQGSRYiLvFWjM/edit#gid=0)"
            await message.channel.send(
                f"{message.author.mention} シートのリンクだ…よ",
                embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # 指定チャンネル以外は無視
        # TODO: 設定ファイルに避ける
        if payload.channel_id != 686701653369683994:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        # メッセージの取得
        reaction_msg = await channel.fetch_message(payload.message_id)

        # リアクション数判定
        reactions = [r for r in reaction_msg.reactions if r.count == 5]
        if len(reactions) < 1:
            return

        send_channel = None
        # NOTE: メッセージ履歴を1分後より前から検索するためのtimedelta
        td = datetime.timedelta(minutes=1)

        # メッセージ履歴を取得
        async for msg in channel.history(
                limit=24,
                before=reaction_msg.created_at + td):
            if msg.author != reaction_msg.author:
                continue

            if len(msg.channel_mentions) < 1:
                continue

            # NOTE: 複数のメンションが含まれていたら困るけど対応できないので無視
            send_channel = msg.channel_mentions[0]
            base_msg = msg
            users = await reactions[0].users().flatten()
            # 送信するメッセージの作成
            send_msg = f"{' '.join([m.mention for m in users])}\n"
            if base_msg.id == reaction_msg.id:
                send_msg += base_msg.clean_content
            else:
                send_msg += f'{base_msg.clean_content}\n{reaction_msg.clean_content}'
            send_msg += ' の参加者が揃った…よ'
            await send_channel.send(send_msg)

            break


def setup(bot):
    bot.add_cog(Mention(bot))
