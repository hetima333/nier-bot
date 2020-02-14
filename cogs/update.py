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
        if ctx.author.id != int(os.environ['DEVELOPER_ID']):
            await ctx.send('このコマンドは開発者専用よ')
            return

        await ctx.send('更新を始めるわ！')
        result = subprocess.run(['git', 'pull'])
        await self._reload_extentions(message)
        await ctx.send(f'更新が終わったわ')

    @commands.command(aliases=['りろ', 'リロード'])
    async def reload(self, ctx, *, message: str = 'all'):
        '''
        開発者用コマンド。botの再読み込みを行います。
        '''

        # 開発者以外は更新できないように
        if ctx.author.id != int(os.environ['DEVELOPER_ID']):
            await ctx.send('このコマンドは開発者専用よ。あなたには扱えないわ')
            return

        await self._disconnect_all_voiceclient()

        await ctx.send('再読み込みを始めるわ！')
        await self._reload_extentions(message)
        await ctx.send('再読み込みが終わったわ')

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

    async def _disconnect_all_voiceclient(self):
        # NOTE: かなり無理矢理退出させているので、要改善
        print("全サーバーのVCから切断します")
        async for guild in self.bot.fetch_guilds(limit=150):
            member = await guild.fetch_member(self.bot.user.id)
            if member is not None:
                await member.move_to(None)


def setup(bot):
    bot.add_cog(Update(bot))
