from serial import Serial, SerialException


class Com:
    def __init__(self, port='COM3', baudrate=2400, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.timeout = timeout
        self.LEVEL = 'level'
        self.UPRIGHT = 'upright'

    def get_serial(self):
        try:
            self.serial = Serial(port=self.port, baudrate=self.baudrate)
            self.serial.timeout = self.timeout
            return True
        except SerialException:
            print('can not connect port: '+self.port+' baudrate: '+str(self.baudrate))
            return False

    def write_command(self, command):
        n = self.serial.write(command)
        result_data = self.serial.read(n)
        if len(result_data) > 0:
            result_bytes = [hex(x) for x in result_data]
            print(result_bytes)
            result_list = [int(x, 16) for x in result_bytes]
            print(result_list)
            return result_list
        return 0

    @staticmethod
    def get_command(type_value, degree_value):
        cmd = [0xff, 0x01, 0x00, type_value]
        degree_value = degree_value * 100
        data_h = int(hex(int(degree_value / 256)), 16)
        data_l = int(hex(degree_value % 256), 16)
        cmd.append(data_h)
        cmd.append(data_l)
        n = 0
        for item in cmd[1:]:
            n += item
        checksum = int(hex(n % 256), 16)
        cmd.append(checksum)
        return cmd

    def stop(self):
        if self.serial.isOpen():
            self.serial.close()

    @staticmethod
    def get_level_command(degree_value):
        type_value = 0x4b
        return Com.get_command(type_value, degree_value)

    @staticmethod
    def get_upright_command(degree_value):
        type_value = 0x4d
        return Com.get_command(type_value, degree_value)

# qr = Com()
# a = qr.get_serial()
# print(a)
# cmd = qr.get_upright_command(30)
# qr.write_command(cmd)
# qr.stop()



