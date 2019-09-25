import datetime
import threading
from tkinter import messagebox, filedialog
from tkinter import *
from win32api import GetSystemMetrics
from PIL import Image, ImageTk

from util.camera_util import Camera
from util.pickle_util import PickleDB
from util.decode_util import Decode

COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']


class State:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.click = 0


class QrCode:
    def __init__(self, cam, pk=None):
        self.state = State()
        self.img_path = ''
        self.decoder = Decode()
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
        self.pk = pk

    def gui_arrange(self):

        self.choose_path_btn.place(relx=64.0 / 80, rely=2.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.reconnect_btn.place(relx=62.0 / 80, rely=16.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.take_photo_btn.place(relx=62.0 / 80, rely=22.0 / 50, width=self.btn_width, height=self.btn_height, )

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

    def init_cam(self):
        # 初始化相机并开始取流
        try:
            self.cam.get_device()
            self.cam.connect_camera_by_enum()
            self.cam.start_grabbing()
            return True
        except:
            return False

    def init_devices(self):
        """初始化设备并检测"""
        temp = '出现错误:\n'

        # 创建相机对象
        self.cam = Camera(self)
        ret_cam = self.init_cam()
        # TODO  设置显示曝光时间
        # self.exposure_value.set(self.cam.get_exposure_value())
        if ret_cam:
            self.light_canvas.itemconfig(self.cam_light, fill='green')
        else:
            if ret_cam is not True:
                temp += '相机 '
                self.light_canvas.itemconfig(self.cam_light, fill='red')
            temp += '\n连接失败！请检查设备！'
            messagebox.showwarning(title='警告！', message=temp)


    def main(self):
        self.init_devices()
        # 创建pickle对象
        self.pk = PickleDB()
        file_dir_path = self.pk.get_value_from_key(self.pk.DIR_PATH)
        if file_dir_path != '':
            self.cam.set_photo_path(self.pk.get_value_from_key(self.pk.DIR_PATH))

        self.gui_arrange()
        self.start_cam_thread()
        mainloop()


qr = QrCode('', '')
qr.gui_arrange()
qr.main()
