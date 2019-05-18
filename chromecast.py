import os
import sys
import socket
import http.server
import threading
import time
import cv2
import pychromecast.pychromecast as pychromecast

class Chromecast:
    class MediaHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(client):
            if client.path.split('?')[0] == "/image.png":
                client.send_response(200)
                client.send_header("Content-type", "image/png")
                client.send_header("Cache-Control", "no-cache")
                client.end_headers()
        def do_GET(client):
            if client.path.split('?')[0] == "/image.png":
                client.send_response(200)
                client.send_header("Content-type", "image/png")
                client.send_header("Cache-Control", "no-cache")
                client.end_headers()
                client.wfile.write(cv2.imencode('.png', client.server.custom_media)[1].tostring())
        def log_message(self, format, *args):
            return

    def __init__(self, chromecast_ip, media_server_port = 8080):
        self.chromecast = pychromecast.Chromecast(chromecast_ip)
        self.server = http.server.HTTPServer((socket.gethostbyname(socket.gethostname()), media_server_port), Chromecast.MediaHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.chromecast.wait()
        self.chromecast.quit_app()
        time.sleep(1)
    
    def __del__(self):
        self.server_thread.stop()
        self.chromecast.quit_app()

    def imshow(self, image):
        self.server.custom_media = image
        self.chromecast.media_controller.play_media("http://{}:{}/image.png?t={}".format(*self.server.server_address, int(1000*time.time())), "image/png")


if __name__ == "__main__":
    projector = Chromecast("10.0.0.82")
    img = cv2.imread('lama.jpg')
    projector.imshow(img)
