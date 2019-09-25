import _thread
import cv2
import datetime
import random
import threading
from tkinter import ttk, messagebox, filedialog
import time
from tkinter import *
from win32api import GetSystemMetrics
from PIL import Image, ImageTk
import os
import numpy as np

from util.camera_util import Camera
from util.mysql_util import Database
from util.csv_util import CsvWR
from util.pickle_util import PickleDB
from util.serial_util import Com
from util.socket_util import RobotSocket
from util.thread_util import Job
from util.decode_util import Decode

COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
class State:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.click = 0

class QrCode:
    def __init__(self, cam, database, com, csvwr, job, pk=None):
        self.state = State()
        self.img_path = ''
        self.rect_image_path = ''
        self.exe_path = sys.path[0]+'/source/Debug/zxing-cv.exe'
        self.decoder = Decode()
        self.__stop = True
        self.any_time_suspend_flag = None
        self.flag = True
        self.last_box_value = ''
        self.root = Tk(className='二维码识别(阿黄专用)')
        self.width = 1366  # 主窗口长
        self.height = 736  # 主窗口宽
        self.screen_width = GetSystemMetrics(0)  # 屏幕长
        self.screen_height = GetSystemMetrics(1)  # 屏幕宽
        self.top = (self.screen_height - self.height) / 2  # 主窗口位置
        self.left = (self.screen_width - self.width) / 2
        self.root.geometry(
            str(self.width) + 'x' + str(self.height) + '+' + str(int(self.left)) + '+' + str(int(self.top)))

        # 按钮
        self.choose_path_btn = Button(self.root, command=self.choose_path, activebackground='blue',
                                      activeforeground='white', bd=3,
                                      bg='cyan', text='选择保存路径')
        self.reconnect_btn = Button(self.root, command=self.init_devices, activebackground='blue',
                                    activeforeground='white', bd=3,
                                    bg='cyan', text='重新连接')
        self.take_photo_btn = Button(self.root, command=self.take_photo, activebackground='blue',
                                     activeforeground='white', bd=3,
                                     bg='cyan', text='拍照')
        self.stop_btn = Button(self.root, command=self.stop, activebackground='blue',
                               activeforeground='white', bd=3,
                               bg='cyan', text='停止')
        self.btn_width = 75
        self.btn_height = 30

        # 画布
        self.file_path = 'source/9001.jpg'
        self.filename = None
        self.canvas = Canvas(self.root, height=608, width=912, borderwidth=2, relief=RIDGE)

        # 文本框，显示日志
        self.log_text_frame = Frame(self.root, height=100)
        self.ysb = Scrollbar(self.log_text_frame)
        self.log_text = Text(self.log_text_frame, width=50, height=8, yscrollcommand=self.ysb.set, )
        self.log_text.config(state=DISABLED)
        self.ysb.config(command=self.log_text.yview)

        # 指示灯
        self.indicator_light_frame = Frame(self.root, height=45, width=120, borderwidth=2, relief=RIDGE)
        self.cam_label = Label(self.indicator_light_frame, text='照相机')
        self.com_label = Label(self.indicator_light_frame, text='云台')
        self.slide_way_label = Label(self.indicator_light_frame, text='滑轨')
        self.light_canvas = Canvas(self.indicator_light_frame, height=14, width=100)
        self.cam_light = self.light_canvas.create_oval(17, 2, 27, 12, fill='green')
        self.com_light = self.light_canvas.create_oval(55, 2, 65, 12, fill='green')
        self.slide_way_light = self.light_canvas.create_oval(90, 2, 100, 12, fill='green')

        # 曝光
        self.exposure_value = StringVar()
        # TODO  self.exposure_value.set()
        self.exposure_entry = Entry(self.root, textvariable=self.exposure_value)
        self.exposure_str = Label(self.root, text='曝光时间')
        self.exposure_btn = Button(self.root, command=self.exposure_confirm, activebackground='blue',
                                   activeforeground='white', bd=3,
                                   bg='cyan', text='确认')

        # 实例对象
        self.cam = cam
        self.database = database

        self.com = com
        self.csvwr = csvwr
        self.job = job
        self.pk = pk
        self.robot = None

        self.wind_can_pic = None  # 右侧画布图片
        self.alert_pic = None  # 弹出框图片

        # 弹出框
        self.bboxList = []  # 存放 x,y,w,h
        self.bboxId = None  # 存放单个矩形框
        self.bboxIdList = []  # 存放所有矩形框
        self.hl = None  # 存放
        self.vl = None

        self.window_enter = Toplevel(self.root)
        self.window_enter.geometry('1200x608')
        self.window_enter.title('Rect window')
        # self.window_enter.wm_attributes("-topmost", 1)

        self.pic_frame = Frame(self.window_enter, width=False, height=False)
        self.pic_ysb = Scrollbar(self.window_enter, orient=VERTICAL)
        self.pic_xsb = Scrollbar(self.window_enter, orient=HORIZONTAL)
        self.picPanel = Canvas(self.pic_frame, width=912, height=608, cursor='tcross', scrollregion=(0, 0, 912, 608))
        self.picPanel.config(yscrollcommand=self.pic_ysb.set, xscrollcommand=self.pic_xsb.set, )
        self.picPanel.bind("<Button-1>", self.mouseClick)
        self.picPanel.bind("<Motion>", self.mouseMove)
        self.pic_xsb.config(command=self.picPanel.xview)
        self.pic_ysb.config(command=self.picPanel.yview)
        self.pic_ysb.pack(side=RIGHT, fill=Y, )
        self.pic_xsb.pack(side=BOTTOM, fill=X, )
        self.picPanel.pack(side=LEFT, )
        self.pic_frame.place(x=0, y=0)

        self.boxes_label = Label(self.window_enter, text='Bounding boxes:')
        self.boxes_label.place(x=950, y=20)

        self.list_frame = Frame(self.window_enter)
        self.list_frame.place(x=950, y=40)
        self.list_scrollbar = Scrollbar(self.list_frame, orient=VERTICAL)
        self.listbox = Listbox(self.list_frame, width=22, height=12,yscrollcommand=self.list_scrollbar.set)
        self.listbox.pack(side=LEFT)
        self.list_scrollbar.config(command=self.listbox.yview)
        self.list_scrollbar.pack(side=RIGHT, fill=Y)

        self.btnDel = Button(self.window_enter, text='Delete', command=self.delBBox, width=20)
        self.btnDel.place(x=950, y=270)
        self.btnClear = Button(self.window_enter, text='ClearAll', command=self.clearBBox, width=20)
        self.btnClear.place(x=950, y=310)
        self.rect_img = None
        self.btnDecode = Button(self.window_enter, text='Select & Decode', command=self.decode, width=20)
        self.btnDecode.place(x=950, y=350)
        self.rect_canvas = Canvas(self.window_enter, height=180, width=200)
        self.rect_canvas.place(x=950, y=390)

        self.window_enter.withdraw()
        self.window_enter.protocol('WM_DELETE_WINDOW', self.window_enter.withdraw)

    def gui_arrange(self):

        self.stop_btn.place(relx=52.0 / 80, rely=2.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.choose_path_btn.place(relx=64.0 / 80, rely=2.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.reconnect_btn.place(relx=62.0 / 80, rely=16.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.take_photo_btn.place(relx=62.0 / 80, rely=22.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.stop_btn.place(relx=62.0 / 80, rely=26.0 / 50, width=self.btn_width, height=self.btn_height, )

        self.exposure_str.place(relx=62.0 / 80, rely=30.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.exposure_entry.place(relx=70.0 / 80, rely=30.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.exposure_btn.place(relx=70.0 / 80, rely=34.0 / 50, width=self.btn_width, height=self.btn_height, )

        self.update_canvas()
        self.canvas.place(relx=2.0 / 80, rely=2.0 / 50, )
        # self.canvas_for_img.place(relx=34.0 / 80, rely=10.0 / 50, )
        self.log_text_frame.place(relx=56.0 / 80, rely=38.0 / 50, )
        self.ysb.pack(side=RIGHT, fill=Y)
        self.log_text.pack()

        self.indicator_light_frame.place(relx=60.0 / 80, rely=10.0 / 50)
        self.cam_label.place(x=0, y=0)
        self.com_label.place(x=45, y=0)
        self.slide_way_label.place(x=80, y=0)
        self.light_canvas.place(x=0, y=20)

    def exposure_confirm(self):
        exposure_num = self.exposure_value.get()
        if self.cam:
            self.cam.exposure_time = exposure_num
            self.cam.set_exposure_value()
        else:
            print('set exposure time error:cam is None')

    def write_msg(self, msg='There are None message!'):
        self.log_text.config(state=NORMAL)
        self.log_text.insert('end',
                             '[' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] - ' + str(msg) + '\n')
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)
        # self.log_text.update()

    def select_bottle_by_value(self, bottle_value):
        sql = "select id from box_bottle where bottle_value = '" + bottle_value + "'"
        results = self.database.execute_select(sql)
        print('results--->')
        print(len(results))
        if len(results) == 0:
            return True
        else:
            return False

    def update_canvas(self):
        print(self.file_path)
        img = Image.open(self.file_path)
        ret = img.resize((912, 608), Image.ANTIALIAS)
        self.filename = ImageTk.PhotoImage(ret)
        self.canvas.create_image(0, 0, anchor='nw', image=self.filename)  # 将图片置于画布上

    def update_canvas_from_cam(self, img):
        ret = img.resize((912, 608), Image.ANTIALIAS)
        self.filename = ImageTk.PhotoImage(ret)
        self.canvas.create_image(0, 0, anchor='nw', image=self.filename)  # 将图片置于画布上
        # PhotoImage create local object (in function) which is deleted by garbage collector when you leave function (
        # and you lose image so you get blink).You have to assign this to existing global variable or to existing object
        self.root.obr = self.filename  # 闪烁
        self.canvas.update()

    """
        阿黄专用画布，显示图片
    """

    def mouseClick(self, event):
        abs_x, abs_y = self.picPanel.canvasx(event.x), self.picPanel.canvasy(event.y)
        print(abs_x, abs_y)
        if self.state.click == 0:
            self.state.x, self.state.y = abs_x, abs_y
        else:
            x1, x2 = min(self.state.x, abs_x), max(self.state.x, abs_x)
            y1, y2 = min(self.state.y, abs_y), max(self.state.y, abs_y)
            self.bboxList.append((int(x1), int(y1), int(x2-x1), int(y2-y1)))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.state.click = 1 - self.state.click

    def mouseMove(self, event):
        abs_x, abs_y = self.picPanel.canvasx(event.x), self.picPanel.canvasy(event.y)
        # self.disp.config(text = 'x: %d, y: %d' %(abs_x, abs_y))
        # print('x: %d, y: %d' % (abs_x, abs_y))
        if self.alert_pic:
            if self.hl:
                self.picPanel.delete(self.hl)
            self.hl = self.picPanel.create_line(0, abs_y, self.alert_pic.width(), abs_y, width = 2)
            if self.vl:
                self.picPanel.delete(self.vl)
            self.vl = self.picPanel.create_line(abs_x, 0, abs_x, self.alert_pic.height(), width = 2)
        if 1 == self.state.click:
            if self.bboxId:
                self.picPanel.delete(self.bboxId)
            self.bboxId = self.picPanel.create_rectangle(self.state.x, self.state.y, \
                                                            abs_x,abs_y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.picPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.picPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def decode(self):
        threading.Thread(target=self.decode_rect).start()

    def open_other_frame(self):
        # self.window_enter.update()
        if not self.window_enter:
            self.window_enter = Toplevel(self.root)
            self.root.update()
        img = Image.open(self.img_path)
        ret = img.resize((912, 608), Image.ANTIALIAS)
        self.alert_pic = ImageTk.PhotoImage(ret)
        self.picPanel.create_image(0, 0, anchor='nw', image=self.alert_pic)  # 将图片置于右侧画布上
        self.picPanel.update()
        self.window_enter.deiconify()
        # self.popen_cmd(self.exe_path + ' ' + self.img_path)

    def take_photo_thread(self):
        self.log_text.delete(0, 'end')
        self.img_path = self.cam.take_photo()
        # self.open_other_frame()
        # self.clearBBox()
        # print(photo_path)

    def take_photo(self):

        t = threading.Thread(target=self.take_photo_thread)
        t.start()

    def decode_rect(self):
        now = time.time()
        print('start time-->', end='')
        print(now)
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        img = Image.open(self.img_path)  # 原图
        img_np = np.asarray(img)  # 原图数组
        ratio_y = img_np.shape[0]/608
        ratio_x = img_np.shape[1]/912
        _, y, _, h = [int(i * ratio_y) for i in self.bboxList[idx]]
        x, _, w, _ = [int(i * ratio_x) for i in self.bboxList[idx]]
        rect_np = img_np[y:y + h, x:x + w]  # 截取的图片
        rect_image = Image.fromarray(rect_np)  # 截取后转化成图片
        now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        rannum = random.randint(0, 1000)
        self.rect_image_path = sys.path[0] + '/source/rect_pic_direction/' + "picture" + now_time + "_" + str(rannum) + ".jpg"
        rect_image.save(self.rect_image_path)  # 保存截图

        p_h = 180 / h
        p_w = 200 / w
        p = p_h if p_h <= p_w else p_w
        rect_image = rect_image.resize((int(w * p), int(h * p)), Image.ANTIALIAS)
        self.rect_img = ImageTk.PhotoImage(rect_image)
        self.rect_canvas.create_image(0, 0, anchor='nw', image=self.rect_img)  # 将图片置于画布上

        self.popen_cmd(self.exe_path + ' ' + self.rect_image_path)
        end = time.time()
        print('end time-->', end='')
        print(end)
        print('time consuming-->', end='')
        print(end - now)



    def popen_cmd(self, cmd):
        # cmd = 'F:/PycharmProjects/app/tkGUI/Debug/zxing-cv.exe ' + self.img_path
        # print(cmd)
        # now = time.time()
        # print('start time-->', end='')
        # print(now)
        result = os.popen(cmd)
        text = result.read()
        print(text)
        result.close()
        r = str(text).split()
        msg = r[-1] if r[-1] != 'a' else 'Please retry!'
        # end = time.time()
        # print('end time-->', end='')
        # print(end)
        # print('time consuming-->', end='')
        # print(end - now)
        self.write_msg(self.img_path + '--->' + str(msg))
        print(self.img_path)

    def start_cam_thread(self):
        """开启相机，获取实时图像"""
        # th = threading.Thread(target=self.change)
        th = threading.Thread(target=self.cam.real_time_image)
        th.start()

    def choose_path(self):
        """选择存储路径"""
        # self.filename = filedialog.askopenfilename(initialdir=None)
        dir_path = filedialog.askdirectory(initialdir=None)
        self.pk.set_dir_path(dir_path)
        self.cam.set_photo_path(self.pk.get_dir_path())
        self.csvwr.set_path_parent(self.pk.get_dir_path())
        print(dir_path)

    def thread_suspend(self):
        while self.any_time_suspend_flag:
            i = 10
            while i > 0:
                time.sleep(1)
                print(1)
        # self.any_time_suspend_flag = True

    def any_time_suspend(self):
        """随时暂停"""
        self.any_time_suspend_flag = True
        th = threading.Thread(target=self.thread_suspend)
        th.start()
        th.join()

    def any_time_continue(self):
        self.any_time_suspend_flag = False

    def init_database(self):
        # 初始化数据库
        return self.database.get_connect()

    def init_com(self):
        # 初始化云台
        return self.com.get_serial()

    def init_cam(self):
        # 初始化相机并开始取流
        try:
            self.cam.get_device()
            self.cam.connect_camera_by_enum()
            self.cam.start_grabbing()

            return True
        except:
            return False

    def init_slide_way(self):
        # 初始化单轴机器人
        try:
            self.robot.get_socket()
            return self.robot.connection_flag
        except:
            return False

    def stop(self):
        """急停后停止所有工作"""
        # self.database.close_connect()
        # self.com.stop()
        self.cam.stop()
        self.job.stop()

    def thread_for_stop(self):
        """急停信号获取"""
        while self.__stop:
            # 获取急停标志
            # print('正在获取急停标志...')
            time.sleep(1)
        self.stop()

    def start_thread_for_stop(self):
        """急停线程，一直获取机器传来的急停信号"""
        stop_th = threading.Thread(target=self.thread_for_stop)
        stop_th.start()

    def delete_last_box(self):
        """删除过期数据--暂停的时候调用"""
        now_time = datetime.datetime.now()
        last_time = now_time - datetime.timedelta(minutes=30)
        t = last_time.strftime('%Y-%m-%d %H:%M:%S')
        sql = "update box_bottle set delete_flag = 1 where time > '"+t+"' and box_value = '"+self.last_box_value+"'"
        ret = self.database.execute_update(sql)
        print('共删除'+str(ret)+'条数据...')

    def pause(self):
        """暂停"""
        self.delete_last_box()
        self.job.pause()

    def init_devices(self):
        """初始化设备并检测"""
        temp = '出现错误:\n'
        # 创建数据库对象
        self.database = Database(host='127.0.0.1', port=3306, user='test', password='123456', database_name='test')

        # 创建相机对象
        self.cam = Camera(self)

        # 创建云台对象
        self.com = Com(port='COM3', baudrate=2400)

        # 创建单轴机器人对象
        self.robot = RobotSocket()

        # ret_database = self.init_database()
        ret_database = True
        ret_cam = self.init_cam()
        # TODO  设置显示曝光时间
        # self.exposure_value.set(self.cam.get_exposure_value())
        # ret_cam = True
        # ret_com = self.init_com()
        ret_com = True
        # ret_slide_way = self.init_slide_way()
        ret_slide_way = True
        if ret_database and ret_com and ret_cam and ret_slide_way:
            self.light_canvas.itemconfig(self.cam_light, fill='green')
            self.light_canvas.itemconfig(self.com_light, fill='green')
            self.light_canvas.itemconfig(self.slide_way_light, fill='green')
        else:
            if ret_database is not True:
                temp = temp + '数据库 '
            if ret_cam is not True:
                temp += '相机 '
                self.light_canvas.itemconfig(self.cam_light, fill='red')
            if ret_com is not True:
                temp += '云台 '
                self.light_canvas.itemconfig(self.com_light, fill='red')
            if ret_slide_way is not True:
                temp += '滑轨 '
                self.light_canvas.itemconfig(self.slide_way_light, fill='red')
            temp += '\n连接失败！请检查设备！'
            messagebox.showwarning(title='警告！', message=temp)


    def main(self):
        self.init_devices()

        # 监听单轴机器人对象
        # th_robot = threading.Thread(target=self.robot.wait_for_send_cmd)

        # 创建csv对象
        self.csvwr = CsvWR()

        # 创建pickle对象
        self.pk = PickleDB()
        file_dir_path = self.pk.get_value_from_key(self.pk.DIR_PATH)
        if file_dir_path != '':
            self.cam.set_photo_path(self.pk.get_value_from_key(self.pk.DIR_PATH))
            self.csvwr.set_path_parent(self.pk.get_value_from_key(self.pk.DIR_PATH))

        # th_robot.start()  # 开启单轴机器人监听
        # self.robot.send_command(self.robot.ZERO_POINT)

        self.job = Job(self)
        self.stop_btn.config(command=self.job.change_suspend_flag)

        self.gui_arrange()
        self.start_thread_for_stop()
        self.start_cam_thread()
        mainloop()


qr = QrCode('', '', '', '', '')
qr.gui_arrange()
qr.main()
