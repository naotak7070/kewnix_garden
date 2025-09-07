from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

class DisplayManager:
    def __init__(self, width=128, height=64, scl_pin=1, sda_pin=0):
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.oled = SSD1306_I2C(width, height, i2c)

    def show_interval_mode(self, active_ch, next_triggers, configs, current_time_ms):
        self.oled.fill(0)
        self.oled.text("Mode: interval", 0, 0)

        items = []
        for i, (pin, high_ms, low_ms) in enumerate(configs):
            if i == active_ch:
                continue  # 現在ONのピンは除外
            remaining = max(0, (next_triggers[i] - current_time_ms) // 1000)
            items.append((remaining, pin))

        # 時間が短い順に並び替え、上位5件のみ表示
        items.sort()
        for i, (remaining, pin) in enumerate(items[:5]):
            self.oled.text(f"Pin {pin}: in {remaining}s", 0, 10 + i * 10)

        self.oled.show()

    def show_manual_mode(self, manual_state_list, configs):
        self.oled.fill(0)
        self.oled.text("Mode: manual", 0, 0)

        for i, state in enumerate(manual_state_list[:5]):
            pin = configs[i][0]  # ピン番号だけ取り出す
            status = "ON" if state else "OFF"
            self.oled.text(f"Pin {pin}: {status}", 0, 10 + i * 10)

        self.oled.show()
