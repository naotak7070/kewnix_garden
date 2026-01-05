import network
import time

class WiFiConnector:
    def __init__(self):
        self.wlan_sta = network.WLAN(network.STA_IF) # 子機モード
        self.wlan_ap = network.WLAN(network.AP_IF)   # 親機(AP)モード

    def connect(self, ssid, password, disconnect_ap=True):
        """指定された情報でWi-Fiに接続を試みる"""
        if not ssid or not password:
            return False

        print(f"Connecting to {ssid}...")
        
        # ★ここを変更: 引数がTrueのときだけAPを切る
        if disconnect_ap:
            self.wlan_ap.active(False)
            
        self.wlan_sta.active(True)
        self.wlan_sta.connect(ssid, password)

        # 接続待ち
        max_wait = 15 # 少し長めに
        while max_wait > 0:
            status = self.wlan_sta.status()
            if status < 0 or status >= 3:
                break
            max_wait -= 1
            print('waiting for connection...')
            time.sleep(1)

        if self.wlan_sta.status() == 3:
            ip = self.wlan_sta.ifconfig()[0]
            print('Connected!', ip)
            return ip # ★True/Falseではなく、IPアドレス(文字列)を返すように変更すると便利
        else:
            print('Connection failed.')
            self.wlan_sta.active(False)
            return None

    def start_ap_mode(self, ap_ssid="Kewnix-Setup", ap_password="password123"):
        """APモード（親機）を起動する"""
        print(f"Starting AP Mode: {ap_ssid}")
        self.wlan_sta.active(False)
        self.wlan_ap.active(True)
        self.wlan_ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))

        # APの設定 (SSID, Password)
        self.wlan_ap.config(ssid=ap_ssid, password=ap_password)
        
        print(f"AP Mode Started. IP: {self.wlan_ap.ifconfig()[0]}")
        return self.wlan_ap.ifconfig()[0]