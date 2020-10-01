import os
import subprocess
import traceback

import discord
from discord.ext import commands

import extentions


class Update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['あぷで', 'アップデート'])
    async def update(self, ctx, *, message: str = 'all'):
        '''
        開発者用コマンド。botの更新を行います。
        '''

        # 開発者以外は更新できないように
        if ctx.author.id != 273424184414175234:
            return

        await ctx.send('更新を始める…よ')
        result = subprocess.run(['git', 'pull'])
        await self._reload_extentions(message)
        await ctx.send(f'更新が終わった…よ')

    @commands.command(aliases=['りろ', 'リロード'])
    async def reload(self, ctx, *, message: str = 'all'):
        '''
        開発者用コマンド。botの再読み込みを行います。
        '''

        # 開発者以外は更新できないように
        if ctx.author.id != 273424184414175234:
            return

        await ctx.send('再読み込みを始める…よ')
        await self._reload_extentions(message)
        await ctx.send('再読み込みが終わった…よ')

    async def _reload_extentions(self, message: str):
        reload_list = None
        if message == 'all':
            reload_list = extentions.extentions
        else:
            reload_list = message.split()
            # リストに含まれていないものが指定されていたら取り除く
            for extention in reload_list:
                if extention not in extentions.extentions:
                    print(f'存在しない拡張機能 {extention} は再読み込みの対象から除外されます')
                    reload_list.remove(extention)

        # 拡張機能の再読み込み
        for extention in reload_list:
            try:
                self.bot.reload_extension(f'cogs.{extention}')
                print(f'reload {extention}')
            except Exception:
                traceback.print_exc()


def setup(bot):
    bot.add_cog(Update(bot))
