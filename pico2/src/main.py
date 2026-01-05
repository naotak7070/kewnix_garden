from logic.multipump_controller import MultiPumpController
from display.display_manager import DisplayManager
from hardware.button_gpio import ButtonGpio
from hardware.wifi_connector import WiFiConnector
from lib.config_manager import ConfigManager
import web.web_server
from web.web_server import start_web_server, set_display
import time
import _thread
import sys
import machine # 追加

def main():
    print("--- Kewnix Garden Booting ---")

    # 安全停止
    print("!!! Press Ctrl+C within 3 seconds to STOP !!!")
    try:
        time.sleep(3)
    except KeyboardInterrupt:
        print("Safety Stop triggered!")
        sys.exit()

    # 設定読み込み
    cfg_manager = ConfigManager()
    pump_configs = cfg_manager.get_pumps()
    wifi_conf = cfg_manager.get_wifi_config()

    # ハードウェア初期化
    buttonA = ButtonGpio(pin_number=20)
    buttonB = ButtonGpio(pin_number=21)
    
    # 修正: ボタン初期値を0に固定（起動時の誤反応防止）
    lastA = 0
    lastB = 0

    display = DisplayManager(use_mock=True) # 必要ならFalseへ
    controller = MultiPumpController(pump_configs, display)
    controller.begin()

    set_display(display)
    
    # Wi-Fi接続
    wifi = WiFiConnector()
    ip_address = None
    display.set_wifi_ap_mode()

    if wifi_conf["mode"] == "STA" and wifi_conf["ssid"]:
        print(f"Connecting to {wifi_conf['ssid']}...")
        display.set_wifi_connecting()
        ip_address = wifi.connect(wifi_conf["ssid"], wifi_conf["password"])
        
        if ip_address:
            print(f"Connected! IP: {ip_address}")
            display.set_wifi_connected(ip_address)
            # ★ここで少しIPを見せる時間をとる
            time.sleep(3) 
        else:
            print("Connection failed. Fallback to AP.")
            display.set_wifi_ap_mode()

    if not ip_address:
        print("Starting AP Mode...")
        ip_address = wifi.start_ap_mode(ap_ssid="Kewnix-Setup", ap_password="password123")
        display.set_wifi_ap_mode()

    # Webサーバー起動
    try:
        _thread.start_new_thread(start_web_server, ())
    except Exception as e:
        print(f"Failed to start server: {e}")

    # ==========================================
    # メインループ
    # ==========================================
    while True:
        # 1. Wi-Fi設定リクエスト処理
        if web.web_server.wifi_request:
            req_ssid, req_pass = web.web_server.wifi_request
            web.web_server.wifi_request = None 
            
            print(f"Wi-Fi Request: {req_ssid}")
            display.fill(0)
            display.text("Testing WiFi...", 0, 0)
            display.text(req_ssid, 0, 10)
            display.show()
            
            # 接続テスト (APは切断せずにトライ)
            temp_wifi = WiFiConnector()
            # disconnect_ap=Falseにしておくと、失敗時にAPが生き残る確率が上がる
            new_ip = temp_wifi.connect(req_ssid, req_pass, disconnect_ap=False)
            
            display.fill(0)
            if new_ip:
                display.text("CONNECTED!", 0, 0)
                display.text("IP Address:", 0, 20)
                display.text(new_ip, 0, 35) # ★IPを表示
                display.show()
                
                # 設定保存
                cfg_manager.update_wifi_config(req_ssid, req_pass, mode="STA")
                
                # ★ここが重要: ユーザーがIPをメモするまで待つ (15秒)
                print("Waiting for user to see IP...")
                time.sleep(15)
                
                print("Rebooting...")
                machine.reset()
            else:
                display.text("FAILED!", 0, 0)
                display.text("Wrong Pass?", 0, 20)
                display.text("Try Again", 0, 40)
                display.show()
                time.sleep(5) # エラー表示を見る時間
                # リブートせず、APモードのまま再試行を待つ

        # 2. リブート要求処理 (★新規追加: Webボタンからの要求)
        if web.web_server.reboot_request:
            web.web_server.reboot_request = False # フラグ回収
            
            print("Reboot requested from Web UI")
            display.fill(0)
            display.text("REBOOTING...", 0, 20)
            display.text("Please Wait", 0, 40)
            display.show()
            
            time.sleep(2)
            machine.reset()

        # 3. 通常のボタン・ポンプ制御
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

if __name__ == "__main__":
    main()