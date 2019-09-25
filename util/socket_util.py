import socket
import threading
import time


class RobotSocket:
    def __init__(self, host='192.168.0.3', port=8000):
        self.socket = None
        self.connection_flag = False
        self.host = host
        self.port = port


        self.pause_flag = True
        self.command = ''
        self.cmd_list = ['Zero_Point\r\n', 'P1\r\n',  'P2\r\n', 'P3\r\n']
        self.ZERO_POINT = 'Zero_Point\r\n'
        self.P1_POINT = 'P1\r\n'
        self.P2_POINT = 'P2\r\n'
        self.P3_POINT = 'P3\r\n'

    def get_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)

    def wait_for_send_cmd(self):
        print('start')
        i = 0
        while True:
            connection, address = self.socket.accept()
            print('get connection to address--->'+str(address))
            if i == 0:
                ret = connection.recv(1024)
                print(ret.decode())
                i += 1
                self.connection_flag = True
                self.pause_flag = False
            if '192.168.0.2' == address[0]:
                while self.pause_flag:
                    time.sleep(1)
                connection.send(self.command.encode())
                print('发送完成')
            self.pause_flag = True
            connection.close()
            time.sleep(2)

    def send_command(self, command):
        self.command = command
        print('发送' + self.command)
        self.pause_flag = False


# so = RobotSocket()
# so.get_socket()
# th = threading.Thread(target=so.wait_for_send_cmd)
# th.start()
# so.send_command('')
# for i in range(4):
#     print(i)
#     so.send_command(so.cmd_list[i])
#     time.sleep(2)
