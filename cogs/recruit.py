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
        # 募集を一時停止しているか
        self.pause = False
        # 募集時間
        # TODO: 外部ファイルに避ける
        self.start_time = 21
        self.end_time = 25
        # 募集開始時間
        # TODO: 外部ファイルに避ける
        self.send_time = 12
        # 対応スタンプ一覧
        # TODO: 外部ファイルに避ける
        self.reactions = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣",
                          "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
        # 送信チャンネル
        # TODO: 外部ファイルに避ける
        self.send_channel_id = [
            667228661899984916,
            667228744196423681
        ]
        # 若葉ロール
        # TODO: 外部ファイルに避ける
        self.rookie_role_id = 666990059647533086

        # json読み込み
        self.RECRUIT_FILE = Path('./data/json/recruit.json')
        with self.RECRUIT_FILE.open() as f:
            self.RECRUITS = json.loads(f.read())

        self._task = bot.loop.create_task(self.dispatch_timers())

    def cog_unload(self):
        self._task.cancel()

    @commands.command()
    async def start(self, ctx):
        pass

    async def dispatch_timers(self):
        '''タイマーの発火'''
        try:
            while not self.bot.is_closed():
                # can only asyncio.sleep for up to ~48 days reliably
                # so we're gonna cap it off at 40 days
                # see: http://bugs.python.org/issue20493
                now = datetime.datetime.now()
                expires = datetime.datetime(
                    now.year, now.month, now.day, self.send_time)

                if expires >= now:
                    to_sleep = (expires - now).total_seconds()
                    await asyncio.sleep(to_sleep)
        except asyncio.CancelledError:
            raise
        except (OSError, discord.ConnectionClosed):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.dispatch_timers())

    async def create_recruit(self, channel_id: int) -> None:
        # メッセージを送る
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
        except discord.HTTPException:
            return

        now = datetime.datetime.now()
        dt = now.date().strftime('%Y/%m/%d')
        title = f'{now.month}/{now.day} {self.start_time}時〜{self.end_time}時の募集だよ…'
        embed = discord.Embed(title=title, color=0x8080c0)
        embed.description = "準備してるから…少し待って…ね"
        msg = await channel.send(embed=embed)
        msg_id = str(msg.id)

        # 募集がなければ追加
        if msg_id not in self.RECRUITS:
            self.RECRUITS[msg_id] = {
                'date': dt,
                'channel_id': channel.id,
                'rookie_count': 0,
                'members': {}
            }

        # jsonに記録
        self.update_recruit()

        # 監視
        await self.watch_recruit(msg_id, self.RECRUITS[msg_id])

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
        embed = discord.Embed(title=title, color=0x8080c0)
        embed.description = "準備してるから…少し待って…ね"
        await msg.edit(embed=embed)

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
                    value = f':thinking_face: {count - 5} 人多いよ…\n{value}'
                elif count == 5:
                    value = f':white_check_mark: 参加者が揃ったよ…\n{value}'
                else:
                    value = f':eyes: あと {5-count} 人足りないよ…\n{value}'

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
                await msg.clear_reactions()
                await msg.edit(embed=embed)
                break
            else:
                recruit = self.RECRUITS[msg_id]
                # 初心者ならカウントを増やす
                if self.is_rookie(user):
                    if int(recruit[msg_id]['recruit_count']) > 2:
                        # TODO: DMで参加できなかった旨を送信する？
                        pass
                    else:
                        recruit['rookie_count'] += 1
                # 未参加のユーザーを追加
                members = recruit['members']
                user_id = str(user.id)
                if user_id not in members:
                    members[user_id] = 0

                flg = members[user_id]
                if emoji == '*⃣':
                    if flg == 0:
                        # NOTE: 募集が9時間まで前提のフラグ
                        members[user_id] = 0b111111111
                    else:
                        members[user_id] = 0
                        members.pop(user_id)
                else:
                    emoji_index = self.reactions.index(emoji) - 1
                    members[user_id] = flg ^ (1 << emoji_index)

                self.update_recruit()
                await update_embed()
                await msg.remove_reaction(emoji, user)

    def is_rookie(self, member: discord.Member) -> bool:
        '''初心者かどうか判定する'''
        roles = [x for x in member.roles if x.id == self.rookie_role_id]
        if len(roles) > 0:
            return True
        return False

    @commands.command()
    async def foo(self, ctx):
        await self.create_recruit(ctx.channel.id)


def setup(bot):
    bot.add_cog(Recruit(bot))
