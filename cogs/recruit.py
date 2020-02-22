from discord.ext import commands, tasks
from discord.utils import get
from pathlib import Path
import discord
import asyncio
import datetime
import json
import re
import config


class Recruit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 設定の読み込み
        self.CONFIG_FILE = Path('./data/json/config.json')
        with self.CONFIG_FILE.open() as f:
            # NOTE: 他の設定に影響を及ぼさないようにする
            self.CONFIG = json.loads(f.read())['recruit']
        # json読み込み
        self.RECRUIT_FILE = Path('./data/json/recruit.json')
        with self.RECRUIT_FILE.open() as f:
            self.RECRUITS = json.loads(f.read())

        # 定刻募集用ループ
        self.loop.start()

        # 監視中タスクリスト
        self.watched_tasks = None

        # 既に存在している募集を監視
        loop = asyncio.get_event_loop()
        loop.create_task(self.watch_all_recruits())

    def cog_unload(self):
        self.loop.cancel()

    def update_config(self) -> None:
        '''設定ファイルの更新'''
        with self.CONFIG_FILE.open() as f:
            _config = json.loads(f.read())
        with self.CONFIG_FILE.open('w') as f:
            _config['recruit'] = self.CONFIG
            f.write(json.dumps(_config, ensure_ascii=False, indent=4))

    def update_recruit(self) -> None:
        '''募集をjsonに反映'''
        with self.RECRUIT_FILE.open('w') as f:
            f.write(json.dumps(self.RECRUITS, ensure_ascii=False, indent=4))

    # ====== 設定変更関数群 ======
    @commands.command(aliases=['start'])
    async def resume(self, ctx):
        '''自動募集の再開'''
        await ctx.channel.send(f"自動募集を再開したよ…\n募集を停止する時は、`{config.COMMAND_PREFIX}stop` と入力して…ね")
        self.CONFIG['is_pause'] = False
        self.update_config()

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        '''自動募集の停止'''
        await ctx.channel.send(f"自動募集を停止したよ…\n募集を再開する時は、`{config.COMMAND_PREFIX}start` と入力して…ね")
        self.CONFIG['is_pause'] = True
        self.update_config()

    @commands.command()
    async def check_recruit(self, ctx):
        '''募集チェック関数'''
        await ctx.channel.send("募集内容のチェックを始める…よ…")
        await self.watch_all_recruits()
        await ctx.channel.send("募集内容のチェックが終わった…よ…\n上手くできたかな…？")

    @tasks.loop(seconds=60)
    async def loop(self) -> None:
        if self.CONFIG['is_pause']:
            return

        # 現在の時刻
        now = datetime.datetime.now()
        date = now.strftime('%m/%d')

        # 同日なら返す
        if date == self.CONFIG['last_send_date']:
            return

        dt_str = now.strftime('%Y/%m/%d')
        dt_str += f" {self.CONFIG['send_time']}"
        dt = datetime.datetime.strptime(dt_str, '%Y/%m/%d %H:%M')

        # 現時刻を超えていたら募集を始める
        if now > dt:
            print("募集投稿の開始")
            for v in self.CONFIG['send_channel_id']:
                await self.create_recruit(v)
            self.CONFIG['last_send_date'] = date
            self.update_config()
            await self.watch_all_recruits()

    async def create_recruit(self, channel_id: int) -> None:
        # メッセージを送る
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
        except discord.HTTPException as e:
            print(e)
            return

        now = datetime.datetime.now()
        dt = now.date().strftime('%Y/%m/%d')
        title = f"{now.month}/{now.day} {self.CONFIG['start_time']}時〜{self.CONFIG['end_time']}時の放置狩り募集だよ…"
        embed = discord.Embed(title=title, color=0x8080c0)
        embed.description = "準備してるから…少し待って…ね"
        msg = await channel.send(embed=embed)
        msg_id = str(msg.id)

        if self.CONFIG['start_time'] >= self.CONFIG['end_time']:
            self.CONFIG['end_time'] += 24
        recruit_count = self.CONFIG['end_time'] - self.CONFIG['start_time']

        # 募集がなければ追加
        if msg_id not in self.RECRUITS:
            self.RECRUITS[msg_id] = {
                'date': dt,
                'start_time': self.CONFIG['start_time'],
                'end_time': self.CONFIG['end_time'],
                'channel_id': channel.id,
                'sections': [{'rookie_cnt': 0, 'members': []} for i in range(recruit_count)]
            }

        # jsonに記録
        self.update_recruit()

    async def watch_all_recruits(self) -> None:
        '''全ての募集の監視を行なう'''
        # 監視中のタスクがあれば全てキャンセル
        if self.watched_tasks is not None:
            for t in self.watched_tasks:
                if t.done() is not True:
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(self.watch_recruit(k, v))
                 for k, v in self.RECRUITS.items()]

        # 監視中タスクにする
        self.watched_tasks = tasks

    async def watch_recruit(self, msg_id: str, data) -> None:
        '''募集の監視を行なう'''
        channel_id = data['channel_id']
        # 募集メッセージが消えていないかチェック
        try:
            channel = self.bot.get_channel(channel_id) or (await self.bot.fetch_channel(channel_id))
            msg = await channel.fetch_message(msg_id)
        except discord.HTTPException as e:
            print(e)
            return
        # リアクションを一旦全部消す
        await msg.clear_reactions()

        st = data['start_time']
        et = data['end_time']
        if st >= et:
            et += 24
        recruit_count = et - st
        # スタンプの数以上の募集は不可能
        if recruit_count >= len(self.CONFIG['reactions']):
            return

        dt = datetime.datetime.strptime(data['date'], '%Y/%m/%d')
        title = f'{dt.month}/{dt.day} {st}時〜{et}時の放置狩り募集だよ…'
        embed = discord.Embed(title=title, color=0x8080c0)
        embed.description = "準備してるから…少し待って…ね"
        await msg.edit(embed=embed)

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
                return emoji in self.CONFIG['reactions']

        async def update_embed():
            embed.clear_fields()
            recruit = self.RECRUITS[msg_id]
            for i in range(recruit_count):
                base_time = recruit['start_time'] + i
                name = f"{self.CONFIG['reactions'][i+1]} {base_time}時〜{base_time+1}時"
                value = ""
                section = recruit['sections'][i]
                count = len(section['members'])
                for member_id in section['members']:
                    user = self.bot.get_user(member_id)
                    if user is not None:
                        user_name = user.display_name
                    else:
                        user_name = ""
                    # TODO: 役職でどうこうするならここ
                    value += f'<@!{member_id}>（{user_name}）\n'
                # TODO: 若葉カウントは都度計算？
                name += f"（🍀️： {section['rookie_cnt']}/{self.CONFIG['max_rookie_cnt']}）"
                # 人数によって絵文字切り替え
                # TODO: 人数によって色を変える
                if count > 5:
                    value = f':thinking_face: {count - 5} 人多いよ…\n{value}'
                elif count == 5:
                    value = f':white_check_mark: 参加者が揃ったよ…\n{value}'
                else:
                    value = f':eyes: あと {5 - count} 人足りないよ…\n{value}'

                embed.add_field(name=name, value=value, inline=False)
            await msg.edit(embed=embed)

        # 残り時間を算出
        expires = datetime.datetime(dt.year, dt.month, dt.day, st)
        expires += datetime.timedelta(hours=recruit_count)
        now = datetime.datetime.now()
        remaining_time = (expires - now).total_seconds()

        if remaining_time > 0:
            if recruit_count > 1:
                await msg.add_reaction('*⃣')
            for i in range(recruit_count):
                await msg.add_reaction(self.CONFIG['reactions'][i+1])

            embed.description = "時間帯に対応した番号で参加・キャンセル"
            if st != et - 1:
                embed.description += "\n:asterisk:で全ての時間帯に参加・キャンセルできるよ…"
            await update_embed()

            # リアクション待機ループ
            while not self.bot.is_closed():
                try:
                    # NOTE: reaction_add だとメッセージがキャッシュにないと実行されない
                    # https://discordpy.readthedocs.io/ja/latest/api.html?highlight=wait_for#discord.on_reaction_add
                    payload = await self.bot.wait_for(
                        'raw_reaction_add',
                        timeout=remaining_time,
                        check=check)
                    member = payload.member
                    emoji = str(payload.emoji)
                except asyncio.TimeoutError:
                    break
                else:
                    # NOTE: 押された番号
                    emoji_index = self.CONFIG['reactions'].index(emoji) - 1
                    recruit = self.RECRUITS[msg_id]
                    if emoji_index < 0:
                        self.join_or_cancel_all_recruit(msg_id, member)
                    else:
                        self.join_or_cancel_recruit(
                            msg_id, emoji_index, member)

                    self.update_recruit()
                    await update_embed()
                    await msg.remove_reaction(emoji, member)

        embed.description = "この募集は終了したよ…"
        embed.color = 0x333333
        await msg.clear_reactions()
        await update_embed()

        # 募集が終わったので削除する
        # NOTE: 2重監視されている場合はここでKeyError
        try:
            self.RECRUITS.pop(msg_id)
        except KeyError:
            pass
        self.update_recruit()

    def join_or_cancel_all_recruit(
            self, msg_id, member: discord.Member) -> None:
        '''
        全ての募集に参加またはキャンセル
        どの募集にも参加していなければ全ての募集に参加
        いずれかの募集に参加済みであれば、全ての募集の参加をキャンセル
        '''
        sections = self.RECRUITS[str(msg_id)]['sections']
        section_cnt = len(sections)
        joined_list = [x for x in range(
            section_cnt) if member.id in sections[x]['members']]
        if len(joined_list) > 0:
            # 全ての参加済みの募集から抜ける
            for index in joined_list:
                self.join_or_cancel_recruit(msg_id, index, member)
        else:
            for index in range(section_cnt):
                self.join_or_cancel_recruit(msg_id, index, member)

    def join_or_cancel_recruit(
            self, msg_id, index: int, member: discord.Member) -> None:
        '''募集に参加またはキャンセル'''
        section = self.RECRUITS[str(msg_id)]['sections'][index]
        # 参加の場合
        if member.id not in section['members']:
            if self.is_rookie(member):
                if section['rookie_cnt'] >= self.CONFIG['max_rookie_cnt']:
                    return
                else:
                    section['rookie_cnt'] += 1
            section['members'].append(member.id)
        # キャンセルの場合
        else:
            if self.is_rookie(member):
                section['rookie_cnt'] -= 1
            section['members'].remove(member.id)

    def is_rookie(self, member: discord.Member) -> bool:
        '''初心者かどうか判定する'''
        roles = [x for x in member.roles if x.id ==
                 self.CONFIG['rookie_role_id']]
        if len(roles) > 0:
            return True
        return False


def setup(bot):
    bot.add_cog(Recruit(bot))
