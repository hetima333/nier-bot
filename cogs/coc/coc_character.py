from pathlib import Path
import json
import re


class CocCharacter():
    def __init__(self, json_data):
        self.json_data = json_data

    SKILL_DATA_FILE = Path('../lunalu-bot/data/json/skill_data.json')
    with SKILL_DATA_FILE.open() as f:
        SKILL_DATA = json.loads(f.read())

    # 技能
    def get_skill_value(self, skill_name: str) -> int:
        skill_type = ""
        skill_index = -1
        for k, v in CocCharacter.SKILL_DATA.items():
            for i, item in enumerate(v):
                r = re.fullmatch(f"^{item}$", skill_name)
                if r is not None:
                    skill_type = k
                    skill_index = i
                    break

        if skill_index == -1:
            return -1

        # NOTE: 一部パラメータは例外あり？
        return self.json_data[skill_type + "P"][skill_index]

    # 能力値
    # NOTE: strが型名と被るから能力値は大文字統一にしています
    @property
    def STR(self):
        return self.json_data["NP1"]

    @property
    def CON(self):
        return self.json_data["NP2"]

    @property
    def POW(self):
        return self.json_data["NP3"]

    @property
    def DEX(self):
        return self.json_data["NP4"]

    @property
    def APP(self):
        return self.json_data["NP5"]

    @property
    def SIZ(self):
        return self.json_data["NP6"]

    @property
    def INT(self):
        return self.json_data["NP7"]

    @property
    def EDU(self):
        return self.json_data["NP8"]

    # ここから小文字に戻ります
    @property
    def hp(self):
        return self.json_data["NP9"]

    @property
    def mp(self):
        return self.json_data["NP10"]

    @property
    def start_san(self):
        '''初期SAN値'''
        return self.json_data["NP11"]

    @property
    def current_san(self):
        '''現在SAN値'''
        return self.json_data["SAN_LEFT"]

    @property
    def danger_san(self):
        '''不定領域'''
        return self.json_data["SAN_Danger"]

    @property
    def idea(self):
        return self.json_data["NP12"]

    @property
    def luck(self):
        return self.json_data["NP13"]

    @property
    def knowledge(self):
        return self.json_data["NP14"]

    # パーソナルデータ

    @property
    def name(self):
        return self.json_data["pc_name"]

    @property
    def job(self):
        return self.json_data["shuzoku"]

    @property
    def age(self):
        return self.json_data["age"]

    @property
    def gender(self):
        return self.json_data["sex"]

    @property
    def height(self):
        return self.json_data["pc_height"]

    @property
    def weight(self):
        return self.json_data["pc_weight"]

    @property
    def birth_place(self):
        return self.json_data["pc_kigen"]

    # TODO: 髪色など追加

    @property
    def memo(self):
        return self.json_data["pc_making_memo"]
