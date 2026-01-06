# lib/presets.py

# 栽培プリセットの定義
# name: 表示名
# on_sec: ポンプON時間(秒)
# off_min: ポンプOFF時間(分)

GARDEN_PRESETS = [
    {
        "id": "std1",
        "name": "Standard 1",
        "on_sec": 5,
        "off_min": 15
    },
    {
        "id": "std2",
        "name": "Standard 2",
        "on_sec": 5,
        "off_min": 10
    },
    {
        "id": "sdl",
        "name": "Seedlings (Light)",
        "on_sec": 3,
        "off_min": 60
    },
    {
        "id": "exp1",
        "name": "Drought stress 1",
        "on_sec": 5,
        "off_min": 120
    }
]