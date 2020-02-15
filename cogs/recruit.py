from discord.ext import commands, tasks
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
        # 募集時間
        # TODO: 外部ファイルに避ける
        self.start_time = 21
        self.end_time = 25
        # 募集開始時間
        # TODO: 外部ファイルに避ける
        self.send_time = "08:00"
        # 対応スタンプ一覧
        # TODO: 外部ファイルに避ける
        self.reactions = ["*⃣", "1⃣", "2⃣", "3⃣", "4⃣",
                          "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
        # 送信チャンネル
        # TODO: 外部ファイルに避ける
        # self.send_channel_id = [
        #     667228661899984916,
        #     667228744196423681
        # ]
        self.send_channel_id = [
            678259997754523680,
            678260017539055616
        ]
        # 若葉ロール
        # TODO: 外部ファイルに避ける
        # self.rookie_role_id = 666990059647533086
        self.rookie_role_id = 678259897082707969
        # 最大若葉の数
        self.max_rookie_count = 1

        # json読み込み
        self.RECRUIT_FILE = Path('./data/json/recruit.json')
        with self.RECRUIT_FILE.open() as f:
            self.RECRUITS = json.loads(f.read())

        # 募集を一時停止しているか
        self.CONFIG_FILE = Path('./data/json/config.json')
        with self.CONFIG_FILE.open() as f:
            self.CONFIG = json.loads(f.read())

        # 定刻募集用ループ
        self.loop.start()

    def cog_unload(self):
        self.loop.cancel()

    @commands.command(aliases=['start'])
    async def resume(self, ctx):
        self.update_pause(False)

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        self.update_pause(True)

    def update_pause(self, flg: bool):
        recruit = self.CONFIG['recruit']['is_pause']
        recruit['is_pause'] = flg

    @tasks.loop(seconds=60)
    async def loop(self) -> None:
        if self.CONFIG['recruit']['is_pause']:
            return

        # 現在の時刻
        now = datetime.datetime.now().strftime('%H:%M')

        if now == f"{self.send_time}":
            await self.create_recruit(self.send_channel_id[0])
            await self.create_recruit(self.send_channel_id[1])
            await self.watch_all_recruits()

    async def create_recruit(self, channel_id: int) -> None:
        # メッセージを送る
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
        except discord.HTTPException:
            return

        now = datetime.datetime.now()
        dt = now.date().strftime('%Y/%m/%d')
        title = f'{now.month}/{now.day} {self.start_time}時〜{self.end_time}時の放置狩り募集だよ…'
        embed = discord.Embed(title=title, color=0x8080c0)
        embed.description = "準備してるから…少し待って…ね"
        msg = await channel.send(embed=embed)
        msg_id = str(msg.id)

        # TODO: 募集時間もjsonに移動させる
        if self.start_time >= self.end_time:
            self.end_time += 24
        recruit_count = self.end_time - self.start_time

        # 募集がなければ追加
        if msg_id not in self.RECRUITS:
            self.RECRUITS[msg_id] = {
                'date': dt,
                'channel_id': channel.id,
                'rookie_count': [0 for i in range(recruit_count)],
                'members': {}
            }

        # jsonに記録
        self.update_recruit()

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

        dt = datetime.datetime.strptime(data['date'], '%Y/%m/%d')
        title = f'{dt.month}/{dt.day} {self.start_time}時〜{self.end_time}時の放置狩り募集だよ…'
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
                return emoji in self.reactions

        async def update_embed():
            embed.clear_fields()
            for i in range(recruit_count):
                base_time = self.start_time + i
                name = f'{self.reactions[i+1]} {base_time}時〜{base_time+1}時'
                mask = 1 << i
                value = ""
                count = 0
                recruit = self.RECRUITS[msg_id]
                members = recruit['members']
                for k, v in members.items():
                    if (v & mask) == mask:
                        # TODO: 役職でどうこうするならここ
                        value += f'<@!{k}>\n'
                        count += 1
                # 若葉用の記述
                name += f"（🍀️： {recruit['rookie_count'][i]}/{self.max_rookie_count}）"
                # 人数によって絵文字切り替え
                # TODO: 人数によって色を変える
                if count > 5:
                    value = f':thinking_face: {count - 5} 人多いよ…\n{value}'
                elif count == 5:
                    value = f':white_check_mark: 参加者が揃ったよ…\n{value}'
                else:
                    value = f':eyes: あと {5-count} 人足りないよ…\n{value}'

                embed.add_field(name=name, value=value, inline=False)
            await msg.edit(embed=embed)

        embed.description = "時間帯に対応した番号で参加・キャンセル"
        if self.start_time != self.end_time - 1:
            embed.description += "\n:asterisk:で全ての時間帯に参加・キャンセルできるよ…"
        self.update_recruit()
        await update_embed()

        # TODO: 残り時間をちゃんと算出する
        # remaining_time = 24 * 60 * 60
        remaining_time = 24

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
                break
            else:
                recruit = self.RECRUITS[msg_id]
                # 未参加のユーザーを追加
                members = recruit['members']
                user_id = str(user.id)
                if user_id not in members:
                    members[user_id] = 0

                flg = members[user_id]
                # NOTE: 何番目がおされた？
                emoji_index = self.reactions.index(emoji) - 1
                if emoji == '*⃣':
                    if flg == 0:
                        if self.is_rookie(user):
                            for i in range(recruit_count):
                                if int(recruit['rookie_count'][i]) < self.max_rookie_count:
                                    recruit['rookie_count'][i] += 1
                                    members[user_id] = members[user_id] ^ (1 << i)
                        else:
                            # NOTE: 募集が9時間まで前提のフラグ
                            members[user_id] = 0b111111111
                    else:
                        if self.is_rookie(user):
                            for i in range(recruit_count):
                                if bin(1 << i) == bin(flg & (1 << i)):
                                    recruit['rookie_count'][i] -= 1
                        members[user_id] = 0
                        members.pop(user_id)
                else:
                    if self.is_rookie(user):
                        # 参加済みか？
                        if bin(1 << emoji_index) == bin(flg & (1 << emoji_index)):
                            members[user_id] = flg ^ (1 << emoji_index)
                            recruit['rookie_count'][emoji_index] -= 1
                        else:
                            if int(recruit['rookie_count'][emoji_index]) < self.max_rookie_count:
                                recruit['rookie_count'][emoji_index] += 1
                                members[user_id] = flg ^ (1 << emoji_index)
                    else:
                        members[user_id] = flg ^ (1 << emoji_index)

                self.update_recruit()
                await update_embed()
                await msg.remove_reaction(emoji, user)

        embed.description = "この募集は終了したよ…"
        await msg.clear_reactions()
        await msg.edit(embed=embed)

        # 募集が終わったので削除する
        self.RECRUITS.pop(msg_id)
        self.update_recruit()

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
