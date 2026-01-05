import json
import os

class ConfigManager:
    FILE_PATH = "config.json"

    def __init__(self):
        self.config = {}
        self.load()

    def load(self):
        """ファイルから設定を読み込む。なければ空の辞書"""
        try:
            with open(self.FILE_PATH, "r") as f:
                self.config = json.load(f)
        except (OSError, ValueError):
            # ファイルがない、または壊れている場合は空にする
            self.config = {}

    def save(self, ssid, password):
        """設定を更新して保存する"""
        self.config["wifi_ssid"] = ssid
        self.config["wifi_password"] = password
        with open(self.FILE_PATH, "w") as f:
            json.dump(self.config, f)
            
    def get_wifi_creds(self):
        """(ssid, password) のタプルを返す。設定がなければ (None, None)"""
        return self.config.get("wifi_ssid"), self.config.get("wifi_password")