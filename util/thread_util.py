import threading
import time
from tkinter import messagebox

from interface.recognition_interface import *


class Job(threading.Thread):

    def __init__(self, qr_code, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()  # 用于暂停线程的标识
        self.__flag.set()  # 设置为True
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True
        self.qr_code = qr_code
        self.sleep_flag = 0
        self.suspend_flag = None

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后返回
            # print(time.time())
            # time.sleep(1)
            # testmed.tp_thread(self.cam, self.database)
            # testmed.my_thread(self.cam, self.database)
            self.main_thread()

    def pause(self):
        self.sleep_flag += 1
        self.__flag.clear()  # 设置为False, 让线程阻塞

    def resume(self):
        self.sleep_flag = 0
        self.__flag.set()  # 设置为True, 让线程停止阻塞

    def stop(self):
        self.__flag.set()  # 将线程从暂停状态恢复, 如果已经暂停的话
        self.__running.clear()  # 设置为False

    def change_suspend_flag(self):
        if self.suspend_flag:
            self.suspend_flag = False

    def save_function(self, case_number):
        for i in range(4):
            for j in range(3):
                self.qr_code.entries[i][j].config(state='disabled', bg='ivory')
        self.save2database(case_number)
        print('手动补录完成')
        self.qr_code.write_msg('手动补录完成')
        print('移动滑轨云台复位')
        self.qr_code.write_msg('移动滑轨云台复位')
        if self.sleep_flag <= 1:
            self.resume()
        self.qr_code.save_entries_btn.config(state='disabled')

    # def sleep(self, msg):
    #     print(msg)
    #     while self.sleep_flag:
    #         time.sleep(1)
    #     self.sleep_flag = True

    def main_thread(self):
        self.qr_code.robot.send_command(self.qr_code.robot.ZERO_POINT)  # 单轴机器人会到原点
        file_path = self.qr_code.cam.take_photo()  # 拍照，获取照片路径
        # file_path = 'jiadelujing'
        '''识别框号'''
        self.qr_code.write_msg('开始识别框号...')
        case_number = case_code(file_path)
        self.qr_code.last_box_value = case_number  # 最后一次识别的框号
        self.qr_code.box_label_value.set('二维码信息:'+case_number)
        self.qr_code.write_msg('识别的框号是:' + case_number)
        '''识别瓶身二维码'''
        self.qr_code.write_msg('开始识别瓶身二维码...')
        bottles_number = [['' for i in range(3)] for i in range(4)]
        for i in range(4):
            self.qr_code.robot.send_command(self.qr_code.robot.cmd_list[i])
            time.sleep(2)
            # 如果不是第一行，则需要调用摄像机拍照
            if i != 0:
                file_path = self.qr_code.cam.take_photo()
                # file_path = 'bushidiyihang'
                print('第' + str(i + 1) + '行调用摄像头拍照')
                self.qr_code.write_msg('第' + str(i + 1) + '行调用摄像头拍照')
            else:
                print('第1行不需要重新调用摄像头')
                self.qr_code.write_msg('第1行不需要重新调用摄像头')
            # 根据照片识别二维码,有不合格的重新拍照识别
            self.filteration(bottles_number, file_path, i)
            self.qr_code.insert_frame(bottles_number)
            # 检查数据库里是否有重复的数据，有的话暂停等待换新瓶子
            for index, bottle_value in enumerate(bottles_number[i]):
                print(index)
                print(bottle_value)
                results = self.qr_code.select_bottle_by_value(bottle_value)
                print(results)
                if not results:
                    # self.suspend_flag = True
                    msg_ret = messagebox.askyesno(title='警告！', message='第' + str(i + 1) + '行第' +
                                                  str(index+1) + '的位置的二维码信息过期，是否暂停更换钢瓶？')
                    if msg_ret:
                        self.suspend_flag = True
                    # self.qr_code.entries[i][index].config(state='normal', bg='green')
                    # self.qr_code.entries[i][index].config(state='disable')
                        while self.suspend_flag:
                            time.sleep(1)
                        new_file_path = self.qr_code.cam.take_photo()  # 重新拍照
                        print('重新拍照了********')
                        # new_file_path = 'adasdad'
                        self.change_bottle_value(bottles_number, new_file_path, i, index)
            # 每完成一行填充一次数据
            self.qr_code.write_msg('第' + str(i + 1) + '行第1列的二维码值是: ' + str(bottles_number[i][0]))
            self.qr_code.write_msg('第' + str(i + 1) + '行第2列的二维码值是: ' + str(bottles_number[i][1]))
            self.qr_code.write_msg('第' + str(i + 1) + '行第3列的二维码值是: ' + str(bottles_number[i][2]))
            self.qr_code.insert_frame(bottles_number)

        # 检查是否有不合格的数据
        flag = True
        for x in range(len(bottles_number)):
            for y in range(len(bottles_number[x])):
                if len(bottles_number[x][y]) < 6:
                    flag = False
                    self.qr_code.entries[x][y].config(bg='red')
                    # break

        if flag:
            self.save2database(case_number)
            print('移动滑轨云台复位')
            self.qr_code.write_msg('移动滑轨云台复位')
        else:
            ret = messagebox.askyesno(title='提示', message='存在不合格数据，是否手动补录？')
            if ret:
                self.qr_code.write_msg('此处存在不合格数据，正在补录')
                self.qr_code.modify_entries()
                self.qr_code.save_entries_btn.config(command=lambda: self.save_function(case_number),
                                                     state='normal')  # 将线程唤醒赋值给按钮
                self.pause()  # 线程暂停
                # self.__flag.wait()
                # _thread.start_new_thread(self.sleep, ('线程暂停',))
                print("手动补录中.....")

    def change_bottle_value(self, bottles_number, file_path, i, index):
        bottles = bottle_codes(file_path)
        for bottle in bottles:
            if bottle not in bottles_number[i]:
                bottles_number[i][index] = bottle

    def filteration(self, bottles_number, file_path, i):
        print('**************************************************************')
        bottles = bottle_codes(file_path)
        print(bottles)
        bottles_number[i][0] = bottles[0]
        bottles_number[i][1] = bottles[1]
        bottles_number[i][2] = bottles[2]
        if len(bottles[0]) < 6:
            print("向左倾斜角度拍照")
            cmd = self.qr_code.com.get_upright_command(30)
            ret = self.qr_code.com.write_command(cmd)
            if ret:
                left_photo_file_path = self.qr_code.cam.take_photo()  # 拍照
                # left_photo_file_path = 'xxsadada'
                left_number = bottle_code(left_photo_file_path)
                bottles_number[i][0] = left_number
                cmd = self.qr_code.com.get_upright_command(0)
                ret = self.qr_code.com.write_command(cmd)
                print("云台角度复位")
            else:
                print('云台调用失败。。。')
        if len(bottles[2]) < 6:
            print("向右倾斜角度拍照")
            cmd = self.qr_code.com.get_upright_command(330)
            ret = self.qr_code.com.write_command(cmd)
            if ret:
                right_photo_file_path = self.qr_code.cam.take_photo()  # 拍照
                # right_photo_file_path = 'adaefs'
                left_number = bottle_code(right_photo_file_path)
                bottles_number[i][2] = left_number
                cmd = self.qr_code.com.get_upright_command(0)
                ret = self.qr_code.com.write_command(cmd)
                print("云台角度复位")
            else:
                print('云台调用失败。。。')

    def save2database(self, case_number):
        # 从entry中获取数据
        self.qr_code.write_msg('保存数据...')
        bottles_number = self.qr_code.save_entries()
        # 如果没有不合格的数据则存储
        sql = self.qr_code.database.add_sql(case_number, bottles_number)
        print(sql)
        ret = self.qr_code.database.execute_update(sql)
        if ret > 0:
            print('数据库保存完成，共' + str(ret) + '条数据')
            self.qr_code.write_msg('数据库保存完成，共' + str(ret) + '条数据')
        # 保存csv
        line = self.qr_code.csvwr.format_data(case_number, bottles_number)
        ret = self.qr_code.csvwr.write_csv(line)
        print(ret)
        if ret:
            print('写入csv成功，文件是:' + ret)
            self.qr_code.write_msg('写入csv成功，文件是:' + ret)
