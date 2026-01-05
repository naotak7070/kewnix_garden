from microdot import Microdot
from lib.config_manager import ConfigManager
from hardware.wifi_connector import WiFiConnector
import machine
from machine import Timer
import _thread
import time

app = Microdot()
config = ConfigManager()

# ディスプレイ操作
display_ref = None
#メインループへの伝言
wifi_request = None
reboot_request = False

def set_display(disp):
    global display_ref
    display_ref = disp

# ==========================================
# HTML テンプレート & ヘルパー
# ==========================================
HTML_HEADER = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Kewnix Garden</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 20px; background-color: #f8f9fa; color: #333; }
        .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }
        h1 { color: #2c3e50; font-size: 24px; margin-bottom: 20px; }
        h3 { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 30px; }
        
        /* フォーム部品 */
        .pump-card { background: #f1f3f5; border-radius: 8px; padding: 15px; margin-bottom: 15px; text-align: left; border-left: 5px solid #007bff; }
        .form-group { margin-bottom: 10px; }
        label { display: inline-block; width: 100px; font-weight: bold; }
        input[type=number] { width: 80px; padding: 5px; border: 1px solid #ccc; border-radius: 4px; }
        input[type=checkbox] { transform: scale(1.5); margin-right: 10px; }
        
        /* ボタン */
        .btn { display: inline-block; background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; font-size: 16px; width: 100%; box-sizing: border-box; margin-top: 10px; }
        .btn-green { background-color: #28a745; }
        .btn-gray { background-color: #6c757d; }
        .btn:hover { opacity: 0.9; }
    </style>
</head>
<body><div class="container">
"""
HTML_FOOTER = "</div></body></html>"

@app.route('/')
def index(request):
    return HTML_HEADER + """
    <h1>Kewnix Garden</h1>
    <p>Dashboard & Settings</p>
    
    <a href="/pumps" class="btn btn-green">Pump Settings</a>
    <a href="/setup" class="btn">Wi-Fi Setup</a>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

# ==========================================
# Wi-Fi 設定 (既存)
# ==========================================
@app.route('/setup')
def setup(request):
    return HTML_HEADER + """
    <h1>Wi-Fi Setup</h1>
    <form action="/save_wifi" method="post">
        <div style="text-align:left; margin-bottom:15px;">
            <label>SSID:</label><br>
            <input type="text" name="ssid" placeholder="Wi-Fi Name" required style="width:100%; padding:8px;">
        </div>
        <div style="text-align:left; margin-bottom:15px;">
            <label>Password:</label><br>
            <input type="text" name="password" placeholder="Password" required style="width:100%; padding:8px;">
        </div>
        <input type="submit" class="btn" value="Save & Connect">
    </form>
    <br>
    <a href="/" class="btn btn-gray">Back</a>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

@app.route('/save_wifi', methods=['POST'])
def save_wifi(request):
    global wifi_request
    form_data = request.form
    ssid = form_data.get('ssid')
    password = form_data.get('password')

    if ssid and password:
        config.update_wifi_config(ssid, password, mode="STA")
        wifi_request = (ssid, password)
        return HTML_HEADER + f"""
        <h1 style="color: #28a745;">Wi-Fi Saved!</h1>
        <p>Connecting to <strong>{ssid}</strong>...</p>
        <p>Check the device screen.</p>
        <hr>
        <form action="/reboot" method="post">
             <input type="submit" class="btn btn-green" value="Reboot Device">
        </form>
        """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}
    return "Error: Missing Data", 400

# ==========================================
# ポンプ設定
# ==========================================
@app.route('/pumps')
def pump_settings(request):
    pumps = config.get_pumps()
    
    html = HTML_HEADER + "<h1>Pump Settings</h1><form action='/pumps/save' method='post'>"
    
    for i, p in enumerate(pumps):
        pin = p['pin']
        enabled = p.get('enabled', True)
        high_sec = int(p['high_ms'] / 1000)      # ms -> 秒
        low_min = int(p['low_ms'] / 1000 / 60)   # ms -> 分
        
        checked = "checked" if enabled else ""
        
        # 各ポンプのカードを生成
        html += f"""
        <div class="pump-card">
            <div class="form-group">
                <input type="checkbox" name="enabled_{i}" value="1" {checked}>
                <strong>Pin {pin}</strong>
            </div>
            <div class="form-group">
                <label>ON (sec):</label>
                <input type="number" name="high_{i}" value="{high_sec}" min="1">
            </div>
            <div class="form-group">
                <label>OFF (min):</label>
                <input type="number" name="low_{i}" value="{low_min}" min="1">
            </div>
            <input type="hidden" name="pin_{i}" value="{pin}">
        </div>
        """
    
    html += """
        <input type="submit" class="btn btn-green" value="Save Configuration">
        </form>
        <br>
        <a href="/" class="btn btn-gray">Back</a>
    """ + HTML_FOOTER
    
    return html, 200, {'Content-Type': 'text/html'}

@app.route('/pumps/save', methods=['POST'])
def save_pumps(request):
    # 現在の設定を取得（ベースにする）
    current_pumps = config.get_pumps()
    new_pumps = []
    
    # フォームデータを解析してリストを再構築
    for i in range(len(current_pumps)):
        # ピン番号は変更せず維持
        pin = current_pumps[i]['pin']
        
        # フォーム値の取得 (存在しなければNone)
        enabled_val = request.form.get(f"enabled_{i}")
        high_val = request.form.get(f"high_{i}")
        low_val = request.form.get(f"low_{i}")
        
        # 型変換と単位変換 (UI:秒/分 -> 内部:ms)
        is_enabled = True if enabled_val else False
        high_ms = int(high_val) * 1000
        low_ms = int(low_val) * 60 * 1000
        
        new_pumps.append({
            "pin": pin,
            "enabled": is_enabled,
            "high_ms": high_ms,
            "low_ms": low_ms
        })
    
    # 保存
    config.save_pumps(new_pumps)
    
    return HTML_HEADER + """
    <h1 style="color: #28a745;">Configuration Saved!</h1>
    <p>Settings have been updated.</p>
    <p>Please reboot to apply changes safely.</p>
    <hr>
    <form action="/reboot" method="post">
         <input type="submit" class="btn btn-green" value="Reboot Device Now">
    </form>
    <br>
    <a href="/pumps" class="btn btn-gray">Back to Edit</a>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

# ==========================================
# 共通処理
# ==========================================

@app.route('/reboot', methods=['POST'])
def reboot_device(request):
    global reboot_request
    # フラグを立てる
    reboot_request = True
    
    return HTML_HEADER + """
    <h1>Rebooting...</h1>
    <p>The device is restarting.</p>
    <p>Please wait about 20 seconds.</p>
    
    <a href="/" class="btn btn-green">Go to Dashboard</a>

    <script>
        setTimeout(function(){
            window.location.href = "/";
        }, 20000);
    </script>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

def start_web_server():
    print("Starting Web Server...")
    app.run(port=80, debug=True)