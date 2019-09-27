import datetime
import threading
import time
from tkinter import messagebox, filedialog
from tkinter import *
from win32api import GetSystemMetrics
from PIL import Image, ImageTk

from util.camera_util import Camera
from util.pickle_util import PickleDB
from util.decode_util import Decode


class QrCode:
    def __init__(self, cam, pk=None):
        self.boxes = []
        self.texts = []
        self.img_path = ''
        self.decoder = Decode()
        self.decode_flag = False
        self.root = Tk(className='二维码识别(Beat)')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.width = 1366  # 主窗口长
        self.height = 736  # 主窗口宽
        self.screen_width = GetSystemMetrics(0)  # 屏幕长
        self.screen_height = GetSystemMetrics(1)  # 屏幕宽
        self.top = (self.screen_height - self.height) / 2  # 主窗口位置
        self.left = (self.screen_width - self.width) / 2
        self.root.geometry(
            str(self.width) + 'x' + str(self.height) + '+' + str(int(self.left)) + '+' + str(int(self.top)))
        self.root.bind('<Escape>', lambda e: self.on_closing())
        self.root.bind('<Return>', lambda e: self.exposure_confirm())
        # 创建一个菜单栏，这里我们可以把他理解成一个容器，在窗口的上方
        self.menubar = Menu(self.root)

        # 定义一个空菜单单元
        self.filemenu = Menu(self.menubar, tearoff=0, borderwidth=2, relief='raised')

        # 将上面定义的空菜单命名为`File`，放在菜单栏中，就是装入那个容器中
        self.menubar.add_cascade(label='选项', menu=self.filemenu)
        self.menubar.add_command(label='开始', command=self.start_cam_thread)
        self.menubar.config()
        a = self.menubar.add_command(label='解码', command=self.change_decode_flag)
        print(a)
        self.menubar.add_command(label='拍照', command=self.take_photo)
        self.menubar.add_command(label='工具', command=None)
        self.menubar.add_command(label='帮助', command=None)

        self.filemenu.add_command(label='开始', command=self.start_cam_thread)
        self.filemenu.add_command(label='拍照', command=self.take_photo)  ##同样的在`File`中加入`Open`小菜单
        self.filemenu.add_command(label='重新连接', command=self.init_cam)
        self.filemenu.add_command(label='选择保存路径', command=self.choose_path)  ##同样的在`File`中加入`Save`小菜单

        self.filemenu.add_separator()  # 分割线

        # 退出
        self.filemenu.add_command(label='退出', command=self.on_closing)

        self.root.config(menu=self.menubar)

        self.btn_width = 75
        self.btn_height = 30

        # 画布
        self.file_path = sys.path[0]+'/source/9001.jpg'
        self.filename = None
        self.canvas_width = 912
        self.canvas_height = 608
        self.canvas = Canvas(self.root, height=600, width=900, borderwidth=2, relief=RIDGE)

        # 文本框，显示日志
        self.log_text_frame = Frame(self.root, height=100)
        self.ysb = Scrollbar(self.log_text_frame)
        self.log_text = Text(self.log_text_frame, width=50, height=20, yscrollcommand=self.ysb.set, )
        self.log_text.config(state=DISABLED)
        self.ysb.config(command=self.log_text.yview)

        # 解码时间
        self.decode_time_value = StringVar()
        self.decode_time_entry = Entry(self.root, textvariable=self.decode_time_value, state=DISABLED)
        self.decode_time__str = Label(self.root, text='解码时间（ms）')
        # 曝光
        self.exposure_value = StringVar()
        # TODO  self.exposure_value.set()
        self.exposure_entry = Entry(self.root, textvariable=self.exposure_value)
        self.exposure_str = Label(self.root, text='曝光时间（us）')
        self.exposure_btn = Button(self.root, command=self.exposure_confirm, activebackground='blue',
                                   activeforeground='white', bd=3,
                                   bg='cyan', text='确认')

        self.take_photo_and_decode_btn = Button(self.root, command=self.take_photo, activebackground='blue',
                                                activeforeground='white', bd=3,
                                                bg='cyan', text='拍照并解码')

        # 实例对象
        self.cam = cam
        self.pk = pk

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.quit()

    def gui_arrange(self):

        self.decode_time__str.place(relx=62.0 / 80, rely=26.0 / 50, width=100, height=self.btn_height, )
        self.decode_time_entry.place(relx=70.0 / 80, rely=26.0 / 50, width=self.btn_width, height=self.btn_height, )

        self.exposure_str.place(relx=62.0 / 80, rely=30.0 / 50, width=100, height=self.btn_height, )
        self.exposure_entry.place(relx=70.0 / 80, rely=30.0 / 50, width=self.btn_width, height=self.btn_height, )
        self.exposure_btn.place(relx=70.0 / 80, rely=34.0 / 50, width=self.btn_width, height=self.btn_height, )

        self.take_photo_and_decode_btn.place(relx=70.0 / 80, rely=38.0 / 50, width=self.btn_width, height=self.btn_height, )

        self.canvas.place(relx=2.0 / 80, rely=2.0 / 50, )
        self.log_text_frame.place(relx=56.0 / 80, rely=2.0 / 50, )
        self.ysb.pack(side=RIGHT, fill=Y)
        self.log_text.pack()

    def exposure_confirm(self):
        exposure_num = self.exposure_value.get()
        if self.cam:
            self.cam.exposure_time = exposure_num
            self.cam.set_exposure_value()
        else:
            print('set exposure time error:cam is None')

    def show_decode_time(self, decode_time):
        self.decode_time_entry.config(state=NORMAL)
        self.decode_time_value.set(float(decode_time) * 1000)
        self.decode_time_entry.config(state=DISABLED)

    def write_msg(self, msg='There are None message!'):
        self.log_text.config(state=NORMAL)
        self.log_text.insert('end',
                             '[' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] - ' + str(msg) + '\n')
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)

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

    def drawQR(self, bounds):
        x_p = self.canvas_width / self.decoder.width
        y_p = self.canvas_height / self.decoder.height
        for idx, bound in enumerate(bounds):
            code = self.decoder.ResultList[idx].res_str.value.decode()
            self.write_msg(str(idx) + ':' + code)
            box = self.canvas.create_polygon(int(bound[0][0] * x_p + 150), int(self.canvas_height - bound[0][1] * y_p),
                                             int(bound[1][0] * x_p + 150), int(self.canvas_height - bound[1][1] * y_p),
                                             int(bound[2][0] * x_p + 150), int(self.canvas_height - bound[2][1] * y_p),
                                             int(bound[3][0] * x_p + 150), int(self.canvas_height - bound[3][1] * y_p),
                                             outline='blue', fill='')
            text = self.canvas.create_text(int(bound[0][0] * x_p + 250), int(self.canvas_height - bound[0][1] * y_p - 15),
                                           text=code, fill='blue', font=30)
            self.texts.append(text)
            self.boxes.append(box)

    def take_photo_thread(self):
        self.log_text.delete(0, 'end')
        self.img_path = self.cam.take_photo()

    def take_photo(self):
        t = threading.Thread(target=self.take_photo_thread)
        t.start()

    def start_cam_thread(self):
        """开启相机，获取实时图像"""
        th = threading.Thread(target=self.cam.real_time_image)
        th.start()

    def change_decode_flag(self):
        if self.decode_flag:
            self.decode_flag = False
            self.menubar.delete(3)
            label = '继续解码'
        else:
            self.decode_flag = True
            self.menubar.delete(3)
            label = '暂停解码'
        self.menubar.insert_command(3, command=self.change_decode_flag, label=label)

    def choose_path(self):
        """选择存储路径"""
        dir_path = filedialog.askdirectory(initialdir=None)
        self.pk.set_dir_path(dir_path)
        self.cam.set_photo_path(self.pk.get_dir_path())
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
        # ret_cam = self.init_cam()
        ret_cam = True
        # TODO  设置显示曝光时间
        # self.exposure_value.set(self.cam.get_exposure_value())
        # self.cam.getIP()

    def main(self):
        self.init_devices()
        # 创建pickle对象
        self.pk = PickleDB()
        file_dir_path = self.pk.get_value_from_key(self.pk.DIR_PATH)
        if file_dir_path != '':
            self.cam.set_photo_path(self.pk.get_value_from_key(self.pk.DIR_PATH))

        self.gui_arrange()
        self.update_canvas()
        # self.start_cam_thread()
        mainloop()


qr = QrCode('', '')
qr.gui_arrange()
qr.main()
