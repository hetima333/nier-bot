from discord.ext import commands
from discord.utils import get
from pathlib import Path
import discord
import asyncio
import datetime
import json
import re


class Recruit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 募集開始時間
        # TODO: 外部ファイルに避ける
        self.start_time = 21
        self.end_time = 25
        # 対応スタンプ一覧
        # TODO: 外部ファイルに避ける
        self.reactions = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣",
                          "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]

        # json読み込み
        self.RECRUIT_FILE = Path('./data/json/recruit.json')
        with self.RECRUIT_FILE.open() as f:
            self.RECRUITS = json.loads(f.read())

    @commands.Cog.listener()
    async def on_ready(self):
        await self.watch_all_recruits()

    def update_recruit(self) -> None:
        '''募集をjsonに反映'''
        with self.RECRUIT_FILE.open('w') as f:
            f.write(json.dumps(self.RECRUITS, ensure_ascii=False, indent=4))

    async def watch_all_recruits(self) -> None:
        '''全ての募集の監視を行なう'''
        cors = [self.watch_recruit(k, v)
                for k, v in self.RECRUITS.items()]
        results = await asyncio.gather(*cors)
        return results

    async def watch_recruit(self, msg_id: str, data) -> None:
        '''募集の監視を行なう'''
        channel_id = data['channel_id']
        # 募集メッセージが消えていないかチェック
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
            msg = await channel.fetch_message(msg_id)
        except discord.HTTPException:
            print('メッセージが削除されています')
            return
        # リアクションを一旦全部消す
        await msg.clear_reactions()

        now = datetime.datetime.now()

        if self.start_time >= self.end_time:
            self.end_time += 24
        recruit_count = self.end_time - self.start_time
        # NOTE: 10時間以上の募集は未対応、スタンプを追加することで対応可能
        if recruit_count > 9:
            return

        # TODO: 募集の日付はjsonに記録しておく
        month = now.month
        day = now.day
        title = f'{month}/{day} 放置狩り {self.start_time}時〜{self.end_time}時'
        embed = discord.Embed(title=title, color=0xFF0000)
        embed.description = "準備中だ…少し待て"
        await msg.edit(embed=embed)
        # 募集がなければ追加
        if msg_id not in self.RECRUITS:
            self.RECRUITS[msg_id] = {
                'channel_id': msg.channel.id,
                'members': {}
            }

        if recruit_count > 1:
            await msg.add_reaction('*⃣')
        for i in range(recruit_count):
            await msg.add_reaction(self.reactions[i+1])

        def check(payload):
            emoji = str(payload.emoji)
            member = payload.member
            if member is None:
                pass
            elif member.bot is True:    # botは無視
                pass
            elif payload.message_id != int(msg_id):
                pass
            else:
                return emoji in self.reactions or emoji == '*⃣'

        async def update_embed():
            embed.clear_fields()
            for i in range(recruit_count):
                base_time = self.start_time + i
                name = f'{self.reactions[i+1]} {base_time}時〜{base_time+1}時'
                mask = 1 << i
                value = ""
                count = 0
                members = self.RECRUITS[msg_id]['members']
                for k, v in members.items():
                    if (v & mask) == mask:
                        # TODO: 役職でどうこうするならここ
                        value += f'<@!{k}>\n'
                        count += 1
                # 人数によって絵文字切り替え
                # TODO: 人数によって色を変える
                if count > 5:
                    value = f':thinking_face: {count - 5} 人多いよ\n{value}'
                elif count == 5:
                    value = f':white_check_mark: 参加者が揃ったよ\n{value}'
                else:
                    value = f':eyes: あと {5-count} 人足りないよ\n{value}'

                embed.add_field(name=name, value=value)
            await msg.edit(embed=embed)

        embed.description = "時間帯に対応した番号で参加・キャンセル"
        if self.start_time != self.end_time - 1:
            embed.description += "\n:asterisk:で全ての時間帯に参加・キャンセル"
        self.update_recruit()
        await update_embed()

        # TODO: 残り時間をちゃんと算出する
        remaining_time = 24 * 60 * 60

        # リアクション待機ループ
        while not self.bot.is_closed():
            try:
                # NOTE: reaction_add だとメッセージがキャッシュにないと実行されない
                # https://discordpy.readthedocs.io/ja/latest/api.html?highlight=wait_for#discord.on_reaction_add
                payload = await self.bot.wait_for(
                    'raw_reaction_add',
                    timeout=remaining_time,
                    check=check)
                user = payload.member
                emoji = str(payload.emoji)
            except asyncio.TimeoutError:
                embed.description = "この募集は終了したよ"
                await msg.edit(embed=embed)
                break
            else:
                # 未参加のユーザーを追加
                members = self.RECRUITS[msg_id]['members']
                user_id = str(user.id)
                if user_id not in members:
                    members[user_id] = 0

                flg = members[user_id]
                if emoji == '*⃣':
                    if members[user_id] == 0:
                        # NOTE: 募集が9時間まで前提のフラグ
                        members[user_id] = 0b111111111
                    else:
                        members[user_id] = 0
                        # members.pop(user_id)
                else:
                    emoji_index = self.reactions.index(emoji) - 1
                    members[user_id] = members[user_id] ^ (1 << emoji_index)

                self.update_recruit()
                await update_embed()
                await msg.remove_reaction(emoji, user)

    # @commands.command()
    # async def foo(self, ctx):
    #     reactions = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣",
    #                  "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
    #     now = datetime.datetime.now()

    #     if self.start_time >= self.end_time:
    #         self.end_time += 24
    #     recruit_count = self.end_time - self.start_time
    #     # NOTE: 10時間以上の募集は未対応
    #     if recruit_count > 9:
    #         return

    #     month = now.month
    #     day = now.day
    #     title = f'{month}/{day} 放置狩り {self.start_time}時〜{self.end_time}時'
    #     embed = discord.Embed(title=title, color=0xFF0000)
    #     embed.description = "準備中だ…少し待て"
    #     msg = await ctx.send(embed=embed)
    #     msg_id = str(msg.id)
    #     # 募集がなければ追加
    #     if msg_id not in self.RECRUITS:
    #         self.RECRUITS[msg_id] = {
    #             'channel_id': msg.channel.id,
    #             'members': {}
    #         }

    #     if recruit_count > 1:
    #         await msg.add_reaction('*⃣')
    #     for i in range(recruit_count):
    #         await msg.add_reaction(reactions[i+1])

    #     async def update_embed():
    #         embed.clear_fields()
    #         for i in range(recruit_count):
    #             base_time = self.start_time + i
    #             name = f'{reactions[i+1]} {base_time}時〜{base_time+1}時'
    #             mask = 1 << i
    #             value = ""
    #             count = 0
    #             members = self.RECRUITS[msg_id]['members']
    #             for k, v in members.items():
    #                 if (v & mask) == mask:
    #                     # TODO: 役職でどうこうするならここ
    #                     value += f'<@!{k}>\n'
    #                     count += 1
    #             # 人数によって絵文字切り替え
    #             # TODO: 人数によって色を変える
    #             if count > 5:
    #                 value = f':thinking_face: {count - 5} 人多いよ\n{value}'
    #             elif count == 5:
    #                 value = f':white_check_mark: 参加者が揃ったよ\n{value}'
    #             else:
    #                 value = f':eyes: あと {5-count} 人足りないよ\n{value}'

    #             embed.add_field(name=name, value=value)
    #         await msg.edit(embed=embed)

    #     def check(reaction, user):
    #         emoji = str(reaction.emoji)
    #         if user.bot is True:    # botは無視
    #             pass
    #         elif reaction.message.id != msg.id:
    #             pass
    #         else:
    #             return emoji in reactions or emoji == '*⃣'

    #     embed.description = "時間帯に対応した番号で参加・キャンセル"
    #     if self.start_time != self.end_time - 1:
    #         embed.description += "\n:asterisk:で全ての時間帯に参加・キャンセル"
    #     self.update_recruit()
    #     await update_embed()

    #     # 残り時間の算出
    #     # now = datetime.datetime.now()
    #     # dt = datetime.datetime(
    #     #     year=now.year, month=now.month, day=day, hour=end_time, minute=0)
    #     # remaining_time = (dt - now).seconds
    #     remaining_time = 24 * 60 * 60

    #     while not self.bot.is_closed():
    #         try:
    #             reaction, user = await self.bot.wait_for(
    #                 'reaction_add',
    #                 timeout=remaining_time, check=check)
    #             emoji = str(reaction)
    #         except asyncio.TimeoutError:
    #             embed.description = "この募集は終了したよ"
    #             await msg.edit(embed=embed)
    #             break
    #         else:
    #             # 未参加のユーザーを追加
    #             members = self.RECRUITS[msg_id]['members']
    #             user_id = str(user.id)
    #             if user_id not in members:
    #                 members[user_id] = 0

    #             flg = members[user_id]
    #             if emoji == '*⃣':
    #                 if members[user_id] == 0:
    #                     # NOTE: 募集が9時間まで前提のフラグ
    #                     members[user_id] = 0b111111111
    #                 else:
    #                     members[user_id] = 0
    #                     # members.pop(user_id)
    #             else:
    #                 emoji_index = reactions.index(emoji) - 1
    #                 members[user_id] = members[user_id] ^ (1 << emoji_index)

    #             self.update_recruit()
    #             await update_embed()
    #             await msg.remove_reaction(emoji, user)


def setup(bot):
    bot.add_cog(Recruit(bot))
