from machine import I2C, Pin

try:
    from ssd1306 import SSD1306_I2C
except ImportError:
    SSD1306_I2C = None

class MockSSD1306:
    """OLEDがない時に、あるフリをするダミークラス"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        print(f"[MockDisplay] Initialized ({width}x{height})")

    def fill(self, col):
        pass

    def text(self, string, x, y, col=1):
        # show_interval_modeなどから直接呼ばれた場合用
        print(f"[MockDisp] {string}")

    def show(self):
        print("-" * 20)


class DisplayManager:
    def __init__(self, width=128, height=64, scl_pin=1, sda_pin=0, use_mock=False):
        # まずインスタンス変数として保存する
        self.use_mock = use_mock
        self.oled = None
        self.wifi_status_str = "AP:192.168.4.1(Setup)"
        
        # use_mockがFalse、かつライブラリがある場合だけ実機接続を試す
        if not self.use_mock and SSD1306_I2C is not None:
            try:
                i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
                if not i2c.scan():
                    raise OSError("No I2C device found")
                self.oled = SSD1306_I2C(width, height, i2c)
                print("OLED Display Initialized")
            except Exception as e:
                print(f"Warning: Display init failed ({e}). Using Mock.")
                self.use_mock = True 
                self.oled = MockSSD1306(width, height)
        else:
            self.use_mock = True
            self.oled = MockSSD1306(width, height)

    def set_wifi_connecting(self):
        """接続中の表示にする"""
        self.wifi_status_str = "Connecting..."

    def set_wifi_connected(self, ip_address):
        """接続成功（IP表示）にする"""
        self.wifi_status_str = f"IP: {ip_address}"

    def set_wifi_ap_mode(self):
        """APモード（セットアップ誘導）にする"""
        # IPは固定なのでここで管理してしまう
        self.wifi_status_str = "AP:192.168.4.1(Setup)"

    # Wi-Fi状態を更新するメソッド
    def update_wifi_status(self, text):
        self.wifi_status_str = text
        
    def show_interval_mode(self, active_ch, next_triggers, configs, current_time_ms):
        self.oled.fill(0)
        # ★1行目: Wi-Fiステータス
        self.oled.text(self.wifi_status_str, 0, 0)
        # ★2行目: モード (y=10 にずらす)
        self.oled.text("Mode: interval", 0, 10)

        items = []

        for i, (pin, high_ms, low_ms) in enumerate(configs):
            if i == active_ch:
                continue  # 現在ONのピンは除外
            remaining = max(0, (next_triggers[i] - current_time_ms) // 1000)
            items.append((remaining, pin))

        # 時間が短い順に並び替え、上位5件のみ表示
        items.sort()
        for i, (remaining, pin) in enumerate(items[:5]):
            self.oled.text(f"Pin {pin}: in {remaining}s", 0, 20 + i * 10)

        self.oled.show()    

    def show_manual_mode(self, manual_state_list, configs):
        self.oled.fill(0)
        # ★1行目: Wi-Fiステータス
        self.oled.text(self.wifi_status_str, 0, 0)
        # ★2行目: モード (y=10 にずらす)
        self.oled.text("Mode: manual", 0, 10)

        for i, state in enumerate(manual_state_list[:5]):
            pin = configs[i][0]  # ピン番号だけ取り出す
            status = "ON" if state else "OFF"
            self.oled.text(f"Pin {pin}: {status}", 0, 20 + i * 10)

        self.oled.show()

    # -----------------------------------------------------------
    # Main/Webから呼ばれるラッパーメソッド
    # -----------------------------------------------------------

    def fill(self, color):
        """画面全体を塗りつぶす (0:黒, 1:白)"""
        if not self.use_mock and self.oled:
            self.oled.fill(color)
        else:
            pass

    def text(self, message, x, y):
        """文字を描画バッファに書き込む"""
        if not self.use_mock and self.oled:
            self.oled.text(str(message), x, y)
        else:
            if y == 0: 
                print(f"[Display] {message}")

    def show(self):
        """画面に反映する"""
        if not self.use_mock and self.oled:
            self.oled.show()
        else:
            print("-------------------")

    def power_off(self):
        """画面を消す（省電力）"""
        self.fill(0)
        self.show()