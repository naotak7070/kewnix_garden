from logic.multipump_controller import MultiPumpController
from display.display_manager import DisplayManager
from hardware.button_gpio import ButtonGpio
import time
import _thread
from hardware.wifi_connector import WiFiConnector
import web.web_server
from web.web_server import start_web_server, set_display
from lib.config_manager import ConfigManager
import sys

def main():
    print("--- Kewnix Garden Booting ---")

    # ==========================================
    # 安全停止
    # ==========================================

    print("!!! Press Ctrl+C within 3 seconds to STOP !!!")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("Safety Stop triggered!")
        sys.exit() # プログラムを終了してREPLへ

    # ==========================================
    # ハードウェア設定
    # ==========================================

    # ボタン設定
    buttonA = ButtonGpio(pin_number=20)
    buttonB = ButtonGpio(pin_number=21)

    # ディスプレイ
    display = DisplayManager(use_mock=True)

    # ポンプ設定: pin, ON(ms), OFF(ms)
    min1 = 60 * 1000
    h1 = 60 * min1
    min15 = 15 * min1
    sec5 = 5 * 1000

    pump_configs = [
        (6, sec5, h1),
        (7, sec5, min15),
        (8, sec5, min15),
        (9, sec5, min15),
        (10, sec5, min15),
        # (11, sec5, min15),
        # (12, sec5, min15),
        # (13, sec5, min15),
    ]

    controller = MultiPumpController(pump_configs, display)
    controller.begin()

    set_display(display)
    
    # ==========================================
    # Wi-Fi設定
    # ==========================================
    cfg = ConfigManager()
    ssid, password = cfg.get_wifi_creds()
    
    wifi = WiFiConnector()
    ip_address = None

    # デフォルトはAPモード表示（初期化時に設定済みだが念の為）
    display.set_wifi_ap_mode()

    # 設定があれば接続を試みる
    if ssid and password:
        print(f"Config found. Connecting to {ssid}...")
        
        display.set_wifi_connecting()
        
        if wifi.connect(ssid, password):
            ip_address = wifi.wlan_sta.ifconfig()[0]
            print(f"Connected! IP: {ip_address}")
            
            display.set_wifi_connected(ip_address)
        else:
            print("Connection failed.")
            display.set_wifi_ap_mode()

    # 接続できていなければ APモード（設定モード）起動
    if not ip_address:
        print("Starting AP Mode for Setup...")
        # スマホから探すときのWi-Fi名
        ip_address = wifi.start_ap_mode(ap_ssid="Kewnix-Setup", ap_password="password123")
        print(f"AP Mode Started. Connect to 'Kewnix-Setup' and go to http://{ip_address}")
        display.set_wifi_ap_mode()

    # Webサーバー起動（Core 1で実行）
    try:
        _thread.start_new_thread(start_web_server, ())
    except Exception as e:
        print(f"Failed to start server thread: {e}")


    # ==========================================
    # メインループ(Core 0で実行)
    # ==========================================

    lastA = lastB = 1

    while True:
        if web.web_server.wifi_request:
            # 伝言を受け取る
            req_ssid, req_pass = web.web_server.wifi_request
            web.web_server.wifi_request = None # 伝言を消す（二重実行防止）
            
            print(f"Received Wi-Fi request for: {req_ssid}")
            
            # ディスプレイ更新: テスト中
            display.fill(0)
            display.text("Saving...", 0, 0)
            display.text("Testing Wi-Fi...", 0, 20)
            display.show()
            
            # 少し待つ（スマホへレスポンスを返す時間を稼ぐ）
            time.sleep(2)
            
            # 接続テスト実行（メインスレッドで行うので安全！）
            temp_wifi = WiFiConnector()
            new_ip = temp_wifi.connect(req_ssid, req_pass, disconnect_ap=False)
            
            # 結果表示
            display.fill(0)
            if new_ip:
                display.text("CONNECTED!", 0, 0)
                display.text("IP Address:", 0, 20)
                display.text(new_ip, 0, 40)
            else:
                display.text("FAILED!", 0, 0)
                display.text("Check Pass", 0, 20)
                display.text("Try Again", 0, 40)
            display.show()


        currentA = buttonA.read()
        currentB = buttonB.read()

        if lastA == 1 and currentA == 0:
            controller.switch_mode("interval")

        if lastB == 1 and currentB == 0:
            if controller.mode != "manual":
                controller.switch_mode("manual")
            controller.handle_manual()

        lastA = currentA
        lastB = currentB

        controller.update()
        time.sleep_ms(100)

# 実行
if __name__ == "__main__":
    main()