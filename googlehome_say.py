#!/usr/bin/python3
import http.server
import shutil
import socket
import socketserver
import sys
import threading
import time
from http import HTTPStatus
from io import BytesIO


def get_yandex_ogg(text):
    import subprocess

    ya_process = subprocess.Popen(["/home/melnikov/yandex-cloud/bin/yc", "config", "get", "folder-id"], stdout=subprocess.PIPE)
    folder_id = ya_process.stdout.read().decode().strip()
    ya_process = subprocess.Popen(["/home/melnikov/yandex-cloud/bin/yc", "iam", "create-token"], stdout=subprocess.PIPE)
    iam_token = ya_process.stdout.read().decode().strip()

    voice = 'alena' # if hash(text) % 2 else 'filipp'
    return get_yandex_ogg_with_token(text, folder_id, iam_token)


def get_yandex_ogg_with_token(text, folder_id, iam_token, voice='alena'):
    import requests
    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + iam_token,
    }

    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': voice,
        'folderId': folder_id,
    }

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        return resp.content


def create_yandex_ogg(text):
    bytes = get_yandex_ogg(text)
    f = BytesIO()
    f.write(bytes)
    f.seek(0)
    return f


def get_local_ip(chromecast_ip):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((chromecast_ip, 80))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


def create_gtts_mp3(text, language):
    from gtts import gTTS
    tts = gTTS(text, lang=language)
    f = BytesIO()
    tts.write_to_fp(f)
    f.seek(0)
    return f


def serve_file(f):
    class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(HTTPStatus.OK)
            # self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(f.getbuffer())))
            self.end_headers()
            f.seek(0)
            shutil.copyfileobj(f, self.wfile)

    handler = HTTPRequestHandler
    httpd = socketserver.TCPServer(("", 0), handler)
    port = httpd.socket.getsockname()[1]
    t = threading.Thread(target=httpd.serve_forever)
    t.setDaemon(True)
    t.start()
    return port


def play_url(chromecast_ip, url):
    import pychromecast
    castdevice = pychromecast.Chromecast(chromecast_ip)
    castdevice.wait()
    vol_prec = castdevice.status.volume_level
    castdevice.set_volume(0.0)  # set volume 0 for not hear the BEEEP

    mc = castdevice.media_controller
    mc.play_media(url, "audio/mp3")

    mc.block_until_active()

    mc.pause()  # prepare audio and pause...

    time.sleep(1)
    if vol_prec == 0:
        castdevice.set_volume(0.15)
    else:
        castdevice.set_volume(vol_prec)
    time.sleep(0.2)

    mc.play()

    while not mc.status.player_is_idle:
        time.sleep(0.5)

    mc.stop()

    castdevice.quit_app()


if len(sys.argv) < 4:
    print("Usage: python3 googlehome_say.py <chromecast_ip> <language> <message>")
    sys.exit(1)
chromecast_ip = sys.argv[1]
language = sys.argv[2]
message = ' '.join(sys.argv[3:])
local_ip = get_local_ip(chromecast_ip)
print(f"local_ip: {local_ip}")

#f = create_gtts_mp3(message, language)
f = create_yandex_ogg(message)
print(f"media size: {len(f.getvalue())}")

port = serve_file(f)
print(f"server up at port {port}")

play_url(chromecast_ip, "http://" + local_ip + ":" + str(port))
