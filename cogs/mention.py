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

        if message.content in ['クラフト', 'くらふと']:
            # apex_daily_crafting チャンネルから最新のメッセージを取得する
            craft_channel_id = '762582916348903435'
            craft_channel = await self.bot.fetch_channel(craft_channel_id)

            last_message_id = craft_channel.last_message_id
            if last_message_id is None:
                return
            last_message = await craft_channel.fetch_message(last_message_id)
            if len(last_message.embeds) == 0:
                return
            tweet_embed = last_message.embeds[0]
            if tweet_embed.image is None:
                return

            current_date = datetime.datetime.now()
            send_date = last_message.created_at

            # 3時より前なら1日前の送信まで有効
            if current_date.day == send_date.day or (current_date.hour < 3 and current_date.day - 1 == send_date.day):
                date_text = f"{send_date.month}/{send_date.day}"
                # 該当する画像へのリンク
                img_link = tweet_embed.image.url

                embed = discord.Embed(color=config.DEFAULT_EMBED_COLOR)
                embed.set_author(
                    name=f'{date_text}のクラフト内容',
                    icon_url=self.bot.user.avatar_url)
                embed.set_image(url=img_link)
                await message.channel.send(
                    f"{message.author.mention} {date_text}のクラフトだ…よ",
                    embed=embed)
            else:
                await message.channel.send('クラフト情報が更新されていないの…ごめんなさい…')


def setup(bot):
    bot.add_cog(Mention(bot))
