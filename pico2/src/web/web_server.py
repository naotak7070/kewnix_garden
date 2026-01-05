from microdot import Microdot
from lib.config_manager import ConfigManager
from hardware.wifi_connector import WiFiConnector
import machine
from machine import Timer
import _thread
import time

app = Microdot()
config = ConfigManager()

# ディスプレイ操作用の変数と関数
display_ref = None
wifi_request = None

def set_display(disp):
    global display_ref
    display_ref = disp

# ==========================================
# HTML テンプレート
# ==========================================
HTML_HEADER = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Kewnix Setup</title>
    <style>
        body { font-family: sans-serif; text-align: center; padding: 20px; background-color: #f4f4f4; }
        .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
        input[type=text] { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        .btn { background-color: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; margin-top: 10px; }
        .btn-green { background-color: #28a745; }
        h1 { color: #333; }
    </style>
</head>
<body><div class="container">
"""
HTML_FOOTER = "</div></body></html>"

@app.route('/')
def index(request):
    return HTML_HEADER + """
    <h1>Dashboard</h1>
    <a href="/setup" class="btn">Wi-Fi Setup</a>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

@app.route('/setup')
def setup(request):
    return HTML_HEADER + """
    <h1>Wi-Fi Setup</h1>
    <form action="/save" method="post">
        <label style="float:left">SSID:</label>
        <input type="text" name="ssid" placeholder="Wi-Fi Name" required>
        <label style="float:left">Password:</label>
        <input type="text" name="password" placeholder="Password" required>
        <input type="submit" class="btn" value="Save & Connect">
    </form>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

@app.route('/save', methods=['POST'])
def save_settings(request):
    global wifi_request
    
    form_data = request.form
    ssid = form_data.get('ssid')
    password = form_data.get('password')

    if ssid and password:
        # 1. 設定保存
        config.save(ssid, password)
        
        # 2. wifi_requestに設定を書き込む
        wifi_request = (ssid, password)
        
        # 3. スマホには即レスポンス（これでフリーズ回避）
        return HTML_HEADER + f"""
        <h1 style="color: #28a745;">Saved!</h1>
        <p>Connecting to <strong>{ssid}</strong>...</p>
        <hr>
        <h3>Please check the Device Screen for the result.</h3>
        <p>(Your phone may disconnect momentarily)</p>
        <hr>
        <form action="/reboot" method="post">
             <input type="submit" class="btn btn-green" value="Reboot Device">
        </form>
        <br>
        <a href="/setup" style="color:#666;">Retry Setup</a>
        """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

    else:
        return "Error: Missing SSID or Password", 400

@app.route('/reboot', methods=['POST'])
def reboot_device(request):
    Timer(-1).init(period=1000, mode=Timer.ONE_SHOT, callback=lambda t: machine.reset())
    return HTML_HEADER + """
    <h1>Rebooting...</h1>
    <p>Please connect to the new IP address shown on the device screen.</p>
    """ + HTML_FOOTER, 200, {'Content-Type': 'text/html'}

def start_web_server():
    print("Starting Web Server...")
    app.run(port=80, debug=True)