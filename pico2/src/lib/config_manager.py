import json
import os

class ConfigManager:
    FILE_PATH = "config.json"
    
    # デフォルト設定（ファイルがない場合に使用）
    DEFAULT_CONFIG = {
        "wifi": {
            "ssid": "",
            "password": "",
            "mode": "AP"  # "STA" (子機) or "AP" (親機)
        },
        "pumps": [
            {"pin": 6, "enabled": True, "high_ms": 5000, "low_ms": 60 * 60 * 1000},
            {"pin": 7, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 8, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 9, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 10, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 11, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 12, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
            {"pin": 13, "enabled": True, "high_ms": 5000, "low_ms": 15 * 60 * 1000},
        ]
    }

    def __init__(self):
        self.config = self._load_from_file()

    def _load_from_file(self):
        """ファイルから設定を読み込む。なければデフォルトを作成"""
        try:
            os.stat(self.FILE_PATH)
            with open(self.FILE_PATH, "r") as f:
                return json.load(f)
        except (OSError, ValueError):
            print("Config file not found or corrupted. Creating default.")
            self._save_to_file(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG

    def _save_to_file(self, data):
        """設定をファイルに書き込む"""
        with open(self.FILE_PATH, "w") as f:
            json.dump(data, f)

    # --- Wi-Fi設定 ---
    def get_wifi_config(self):
        """Wi-Fi設定辞書を返す"""
        return self.config.get("wifi", self.DEFAULT_CONFIG["wifi"])

    def update_wifi_config(self, ssid, password, mode="STA"):
        """Wi-Fi設定を更新して保存"""
        self.config["wifi"] = {
            "ssid": ssid,
            "password": password,
            "mode": mode
        }
        self._save_to_file(self.config)
        print("WiFi config saved.")

    # --- ポンプ設定 ---
    def get_pumps(self):
        """ポンプ設定リストを返す"""
        return self.config.get("pumps", self.DEFAULT_CONFIG["pumps"])

    def save_pumps(self, pumps_list):
        """ポンプ設定リストを更新して保存"""
        self.config["pumps"] = pumps_list
        self._save_to_file(self.config)