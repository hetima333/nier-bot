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
        self.start_time = 21
        self.end_time = 25

        # json読み込み
        self.RECRUIT_FILE = Path('')
        with self.RECRUIT_FILE.open() as f:
            self.RECRUITS = json.loads(f.read())

    @commands.command()
    async def foo(self, ctx):
        reactions = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣",
                     "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
        reaction_members = {}
        now = datetime.datetime.now()

        if self.start_time >= self.end_time:
            self.end_time += 24
        recruit_count = self.end_time - self.start_time
        # NOTE: 10時間以上の募集は未対応
        if recruit_count > 9:
            return

        month = now.month()
        day = now.day()
        title = f'{month}/{day} 放置狩り {self.start_time}時〜{self.end_time}時'
        embed = discord.Embed(title=title, color=0xFF0000)
        embed.description = "準備中だ…少し待て"
        msg = await ctx.send(embed=embed)

        if recruit_count > 1:
            await msg.add_reaction('*⃣')
        for i in range(recruit_count):
            await msg.add_reaction(reactions[i+1])

        async def update_embed():
            embed.clear_fields()
            for i in range(recruit_count):
                base_time = self.start_time + i
                name = f'{reactions[i+1]} {base_time}時〜{base_time+1}時'
                mask = 1 << i
                value = ""
                count = 0
                for v in reaction_members.values():
                    if (v['flag'] & mask) == mask:
                        value += v['name'] + '\n'
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

        def check(reaction, user):
            emoji = str(reaction.emoji)
            if user.bot is True:    # botは無視
                pass
            elif reaction.message.id != msg.id:
                pass
            else:
                return emoji in reactions or emoji == '*⃣'

        embed.description = "時間帯に対応した番号で参加・キャンセル"
        if self.start_time != self.end_time - 1:
            embed.description += "\n:asterisk:で全ての時間帯に参加・キャンセル"
        await update_embed()

        # 残り時間の算出
        # now = datetime.datetime.now()
        # dt = datetime.datetime(
        #     year=now.year, month=now.month, day=day, hour=end_time, minute=0)
        # remaining_time = (dt - now).seconds
        remaining_time = 24 * 60 * 60

        while not self.bot.is_closed():
            try:
                reaction, user = await self.bot.wait_for(
                    'reaction_add',
                    timeout=remaining_time, check=check)
                emoji = str(reaction)
            except asyncio.TimeoutError:
                embed.description = "この募集は終了したよ"
                await msg.edit(embed=embed)
                break
            else:
                # 未参加のユーザーを追加
                if user.id not in reaction_members:
                    reaction_members[user.id] = {
                        'name': user.mention,
                        'flag': 0
                    }

                flag = reaction_members[user.id]['flag']
                if emoji == '*⃣':
                    if flag == 0:
                        # NOTE: 募集が9時間まで前提のフラグ
                        reaction_members[user.id]['flag'] = 0b111111111
                    else:
                        reaction_members[user.id]['flag'] = 0
                        reaction_members.pop(user.id)
                else:
                    emoji_index = reactions.index(emoji) - 1
                    reaction_members[user.id]['flag'] = flag ^ (
                        1 << emoji_index)

                await update_embed()
                await msg.remove_reaction(emoji, user)


def setup(bot):
    bot.add_cog(Recruit(bot))
