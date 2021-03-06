import socket
import http.server
import threading
import time

import pychromecast
import cv2

class ImageStreamer:
    class MediaHandler(http.server.BaseHTTPRequestHandler):
        def do_HEAD(self):
            if self.path.split('?')[0] == "/video":
                self.send_response(200)
                self.send_header("Content-type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                
        def do_GET(self):
            if self.path.split('?')[0] == "/video":
                self.send_response(200)
                self.send_header("Content-type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                while self.server._custom_run:
                    try:
                        if self.server._custom_media is not None:
                            frame_data = cv2.imencode('.jpg', self.server._custom_media)[1].tobytes()
                        else:
                            frame_data = bytearray()
                        data = '\r\n--frame\r\nContent-Type: image/jpeg\r\nContent-length: '.encode('utf8')
                        data += str(len(frame_data)).encode('utf8')
                        data += '\r\n\r\n'.encode('utf-8') + frame_data + '\r\n\r\n'.encode('utf-8')
                        self.wfile.write(data)
                    except (ConnectionResetError, ConnectionAbortedError):
                        pass

        def log_message(self, format, *args):
            return

    def __init__(self, server_port = 8080, verbose = True):
        self.verbose = verbose
        self._server = http.server.HTTPServer((socket.gethostbyname(
            socket.gethostname()), server_port), self.MediaHandler)
        self._server._custom_run = False
        self._server._custom_media = None

    def connect(self):
        # start server
        if not self._server._custom_run:
            self._server._custom_run = True
            self._server._custom_media = None
            self._server_thread = threading.Thread(target=self._server.serve_forever)
            self._server_thread.start()
            # print info
            if self.verbose:
                print("streaming at: http://{}:{}/video".format(*self._server.server_address))    

    def disconnect(self):
        # close server
        if self._server._custom_run:
            self._server._custom_run = False
            self._server.shutdown()
            self._server.server_close()
            self._server_thread.join()

    def imshow(self, image):
        self._server._custom_media = image

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, ext_type, exc_value, traceback):
        self.disconnect()

    def __del__(self):
        self.disconnect()

class Chromecast(ImageStreamer):
    def __init__(self, chromecast_ip, media_server_port = 8080, verbose = False):
        super().__init__(server_port=media_server_port, verbose=verbose)
        self.chromecast_ip = chromecast_ip
        self._casting = False

    def connect(self):
        if not self._casting:
            self._casting = True
            # connect media server
            super().connect()
            # connect to chromecast
            self._chromecast = pychromecast.Chromecast(self.chromecast_ip)
            self._chromecast.wait()
            # connect to stream
            self._chromecast.media_controller.play_media(
                "http://{}:{}/video".format(*self._server.server_address), "image/jpeg")

    def disconnect(self):
        if self._casting:
            self._casting = False
            # close chromecast app
            self._chromecast.quit_app()
            # close media server
            super().disconnect()

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, ext_type, exc_value, traceback):
        self.disconnect()

    def __del__(self):
        self.disconnect()

if __name__ == "__main__":
    import numpy as np

    try:
        with Chromecast("10.0.0.82") as cc:
            print("running")
            while True:   
                image = (255 * np.random.rand(256, 256, 3)).astype(np.uint8)
                cc.imshow(image)
    except KeyboardInterrupt:
        print("stopped")
