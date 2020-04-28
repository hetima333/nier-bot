from discord.ext import commands
import discord

from pathlib import Path

# TODO: ダイスロールは別ファイルに移動する
import random
import re
import aiohttp
import io
import json
from cogs.utils.coc.coc_character import CocCharacter


class CocHelper(commands.Cog):
    CHARACTER_DIR = Path('../lunalu-bot/data/json/character')

    def __init__(self, bot):
        self.bot = bot

    # # on_xxxx
    # @commands.Cog.listener()
    # async def on_message(self, message: discord.Message):
    #     if message.author.bot:
    #         return

    #     # urlじゃなかったら早めに返す
    #     if message.content[0] != "h":
    #         return

    #     # NOTE: re使うほどじゃなさそうなので修正したほうがいいかも
    #     url_reg = r"https:\/\/charasheet\.vampire-blood\.net\/\d{1,}"
    #     result = re.match(url_reg, message.content)
    #     if result is None:
    #         return

    #     json_url = result.group() + ".js"
    #     print(json_url)

    #     # データ取得
    #     # async with message.channel.typing():
    #     # NOTE: テスト中はローカルからデータ取得する
    #     json_data = self._load_character_from_json()
    #     character = CocCharacter(json_data)
    #     # print(json.dumps(json_data, indent=4, ensure_ascii=False))
    #     register_message = f"{message.author.mention}\n"
    #     register_message += f"キャラクター **{character.name}** を登録してもいいかしら？"
    #     await message.channel.send(f"{register_message}")

    # command

    @commands.command(aliases=["rs"])
    async def roll_with_skill(self, ctx, skill_name: str = ""):
        # IDを元にキャラクターを読み込み
        pl = CocHelper._load_character_from_json(ctx.author.id)
        roll = self._roll_with_skill(pl, skill_name)

        message = f"{ctx.author.mention}\n{roll}"
        await ctx.channel.send(message)

    @commands.command(aliases=["rc"])
    async def register_character(self, ctx, url: str):
        # NOTE: re使うほどじゃなさそうなので修正したほうがいいかも
        url_reg = r"https:\/\/charasheet\.vampire-blood\.net\/[0-9a-zA-Z]{1,}"
        result = re.match(url_reg, url)
        if result is None:
            await ctx.channel.send("URLが正しくないわ…\n正しいURLは `https://charasheet.vampire-blood.net/00000` のような形式よ")
            return

        data = await self._fetch_character_json_data(url + ".json")
        if data is None:
            await ctx.channel.send("キャラクターデータ取得できなかったわ…公開設定などを見直してみて")
            return

        path = CocHelper.CHARACTER_DIR / f"{ctx.author.id}.json"
        with path.open('w') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=4))

        character = CocCharacter(data)

        await ctx.channel.send(f"{ctx.author.mention} {character.name} をあなたのキャラクターとして登録したわ")

    # asyncメソッド
    async def _fetch_character_json_data(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return json.loads(data)
                else:
                    return None

    # json関連
    @classmethod
    def _load_character_from_json(cls, id: int):
        path = cls.CHARACTER_DIR / f"{id}.json"
        with path.open() as f:
            data = json.load(f)

        # idをつかってプレイヤーに対応したデータを読み込む
        return CocCharacter(data)

    # 非asyncメソッド
    def _add_character(self, url: str):
        pass

    def _reload_character(self):
        pass

    def _select_character(self):
        pass

    def _get_skill_param(self, character: CocCharacter, skill_name: str):
        """
        技能名を指定して技能値を取得
        """
        return character.get_skill_value(skill_name)

    def _roll_with_skill(self, character: CocCharacter, skill_name: str):
        """
        技能名またはステータス名を指定してダイスロール
        TODO: ボーナスを追加できるように
        """

        # 技能が未指定の場合はヘルプを出す
        if skill_name == "":
            return "技能名が指定されていないわ\n次のように指定してみて\n> -rs 目星"

        # 目標値
        goal_num = 0
        # ダイスの数と面数
        dice_face = 100

        # 目標値の取得
        # TODO: このままだとCON * 5 とかできないので考える
        goal_num = int(character.get_skill_value(skill_name))
        if goal_num == -1:
            return f"{skill_name} という技能が存在しないわ…"

        # ダイスロール
        dice_result = random.randint(1, dice_face)

        # 成功判定
        # NOTE: ハウスルールに対応するなら変更の必要あり
        result_text = "失敗"
        if dice_result <= 5:
            result_text = "クリティカル"
        elif dice_result <= goal_num:
            result_text = "成功"
        elif dice_result > 95:
            result_text = "ファンブル"

        # TODO: いい感じに取得する
        character_name = character.name

        # TODO: 正しいスキル名で返す
        result = f"{character_name} の {skill_name} ： {goal_num}\n"
        result += f"```1d{dice_face} = ({dice_result}) = {dice_result}```\n"
        result += f"> **{result_text}**\n"

        return result

    def _roll_dice(self, face, num):
        results = []
        for i in range(num):
            dice = random.randint(1, face)
            results.append(dice)


def setup(bot):
    bot.add_cog(CocHelper(bot))
