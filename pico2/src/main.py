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
import machine
import network

def main():
    # =====================================================
    # 1. 最優先でディスプレイを初期化してロゴを表示
    # =====================================================
    print("--- Kewnix Garden Booting ---")
    
    display = DisplayManager(use_mock=False) 
    display.show_splash() # ロゴ表示
  

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
    
    # ボタン初期値を0に固定（起動時の誤反応防止）
    lastA = 0
    lastB = 0
    # Aボタン長押し判定用の変数を初期化
    btnA_press_start = 0
    ignore_next_release = False
    # Bボタン用変数とWi-Fi状態フラグ
    btnB_press_start = 0
    ignore_next_release_B = False
    is_wifi_on = True  # 起動時はONスタート


    controller = MultiPumpController(pump_configs, display)

    set_display(display)
    
    # Wi-Fi接続
    wifi = WiFiConnector()
    ip_address = None
    display.set_wifi_connecting()
    print("Attempting to connect...")


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
    
    print("Starting Pump Controller...")
    controller.begin()

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

        # 2. リブート要求処理 (Webボタンからの要求)
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

        # === Aボタン処理 (長押し: IP表示 / 短押し: モード切替) ===
        if currentA == 1:
            if lastA == 0:
                # 押し始めの時刻を記録
                btnA_press_start = time.ticks_ms()
            
            # 押されている間の時間をチェック
            if time.ticks_diff(time.ticks_ms(), btnA_press_start) > 2000:
                # 2秒以上経過 -> 情報表示
                print("Show Network Info")
                display.fill(0)
                display.text("--- NETWORK ---", 0, 0)
                
                # ★Wi-Fiの状態によって表示を分岐
                if is_wifi_on:
                    # ONの場合：詳細を表示
                    mode_str = "Unknown"
                    if wifi_conf and isinstance(wifi_conf, dict):
                        mode_str = wifi_conf.get("mode", "AP")
                    display.text(f"Mode: {mode_str}", 0, 20)
                    
                    ip_str = ip_address if ip_address else "No IP"
                    display.text(str(ip_str), 0, 40)
                else:
                    # OFFの場合：ONにする方法を案内
                    display.text("Status: OFF", 0, 20)
                    display.text("(Hold B to ON)", 0, 40)
                
                display.show()
                time.sleep(3)
                
                controller.last_display_refresh = 0
                ignore_next_release = True
                btnA_press_start = time.ticks_ms() + 10000
            

        elif lastA == 1: 
            # ボタンを離した瞬間 (currentA == 0)
            if not ignore_next_release:
                # 長押し処理が行われていなければ、通常のモード切替を実行
                controller.switch_mode("interval")
            
            # フラグをリセット
            ignore_next_release = False
        # ========================================================

        # === Bボタン処理 (長押し: IP表示 / 短押し: モード切替) ===
        if currentB == 1:
            if lastB == 0:
                btnB_press_start = time.ticks_ms()
            
            # 長押し判定 (2秒)
            if time.ticks_diff(time.ticks_ms(), btnB_press_start) > 2000:
                print("Toggle Wi-Fi Power")
                display.fill(0)
                
                if is_wifi_on:
                    # --- Wi-Fi を OFF にする処理 ---
                    display.text("Stopping Wi-Fi...", 0, 0)
                    display.show()
                    
                    # STAとAPの両方を無効化してチップを停止
                    network.WLAN(network.STA_IF).active(False)
                    network.WLAN(network.AP_IF).active(False)
                    
                    is_wifi_on = False
                    ip_address = None
                    
                    display.fill(0)
                    display.text("Wi-Fi: OFF", 0, 20)
                    display.text("(Power Saving)", 0, 40)
                    display.show()
                    
                else:
                    # --- Wi-Fi を ON にする処理 ---
                    display.text("Starting Wi-Fi...", 0, 0)
                    display.show()
                    
                    # 1. 接続を試行 (起動時と同じロジック)
                    if wifi_conf["mode"] == "STA" and wifi_conf["ssid"]:
                        display.text(f"Conn: {wifi_conf['ssid']}", 0, 20)
                        display.show()
                        # 再接続のため新しいインスタンスで試行
                        tmp_wifi = WiFiConnector() 
                        ip_address = tmp_wifi.connect(wifi_conf["ssid"], wifi_conf["password"])
                    
                    # 2. 失敗または未設定ならAPモード
                    if not ip_address:
                        display.fill(0)
                        display.text("Starting AP...", 0, 0)
                        display.show()
                        tmp_wifi = WiFiConnector()
                        ip_address = tmp_wifi.start_ap_mode(ap_ssid="Kewnix-Setup", ap_password="password123")
                    
                    is_wifi_on = True
                    display.fill(0)
                    display.text("Wi-Fi: ON", 0, 0)
                    display.text(str(ip_address), 0, 20)
                    display.show()

                time.sleep(3)
                controller.last_display_refresh = 0
                ignore_next_release_B = True
                btnB_press_start = time.ticks_ms() + 10000

        elif lastB == 1:
            # ボタンを離した瞬間
            if not ignore_next_release_B:
                # 長押ししていなければ、元の機能（ポンプ操作）を実行
                if controller.mode != "manual":
                    controller.switch_mode("manual")
                controller.handle_manual()
            
            ignore_next_release_B = False
        # ========================================================

        lastA = currentA
        lastB = currentB

        controller.update()

        time.sleep_ms(100)

if __name__ == "__main__":
    main()