import datetime
import threading
import time
from tkinter import messagebox, filedialog, ttk
from tkinter import *
from win32api import GetSystemMetrics
from PIL import Image, ImageTk

from util.camera_util import Camera
from util.pickle_util import PickleDB
from util.decode_util import Decode


class QrCode:
    def __init__(self):
        self.boxes = []
        self.texts = []
        self.img_path = ''
        self.decoder = Decode()
        self.decode_flag = False
        self.light_flag = True
        self.codes_num_value = 20
        self.root = Tk(className='条码识别(Beat)')
        self.root.iconbitmap(default=sys.path[0]+'/source/jcst.ico')
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

        self.menubar = Menu(self.root)

        self.filemenu = Menu(self.menubar, tearoff=0, borderwidth=2, relief='raised')
        self.menubar.add_cascade(label='选项', menu=self.filemenu)

        self.menubar.add_command(label='开始', command=self.start_cam_thread)
        self.menubar.add_command(label='解码', command=self.change_decode_flag)
        self.menubar.add_command(label='拍照', command=self.take_photo)
        self.menubar.add_command(label='工具', command=None)
        self.menubar.add_command(label='设置', command=self.setting_config)
        self.menubar.add_command(label='帮助', command=None)

        self.filemenu.add_command(label='开始', command=self.start_cam_thread)
        self.filemenu.add_command(label='拍照', command=self.take_photo)
        self.filemenu.add_command(label='重新连接', command=self.reconnection)
        self.filemenu.add_command(label='选择保存路径', command=self.choose_path)
        self.filemenu.add_separator()  # 分割线
        self.filemenu.add_command(label='退出', command=self.on_closing)  # 退出

        self.root.config(menu=self.menubar)

        self.btn_width = 75
        self.btn_height = 30

        # 画布
        self.file_path = sys.path[0]+'/source/jc-st.jpg'
        self.file_path = sys.path[0]+'/source/jc-st.jpg'
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
        # self.cam = cam
        # self.pk = pk

        # c1.pack()
        # 亮度
        self.scale = Scale(self.root, label='亮度调节（us）', from_=0, to=5000, orient=HORIZONTAL, command=self.get_scale_value, length=900, showvalue=1, tickinterval=1000, resolution=1)
        self.scale.set(1000)  # 设置初始值
        self.scale.place(relx=2.0 / 80, rely=43.0 / 50, )

        # 设置页面
        self.setting_window = Toplevel(self.root)
        self.setting_window.geometry('400x800')
        self.setting_window.title('Settings')
        self.setting_window.withdraw()
        self.setting_window.protocol('WM_DELETE_WINDOW', self.setting_window.withdraw)

        # 多选框 选择不同码
        self.code_str = Label(self.setting_window, text='选择码质:')
        self.code_frame = Frame(self.setting_window, height=50, width=50, borderwidth=2, relief=RIDGE)
        self.codes = ['QR', 'DataMatrix', 'PDF', 'RSS', 'CODE39', 'AZ', 'CB', 'CODE128', 'CODABLOCK_F', 'CODABLOCK_A',
                      'I25', 'MC', 'MICROPDF', 'POSTAL', 'UPC', 'CODE93', 'CC', 'S25_2SS', 'S25_3SS', 'MSIP', 'PHARMA',
                      'C11', 'M25', 'TP', 'NEC25', 'OCR']
        self.codes_values = [0x40010901, 0x40010401, 0x40010701, 0x40011301, 0x40010301, 0x40011201, 0x40010101,
                             0x40010201, 0x40010205, 0x40010305, 0x40010501, 0x40010601, 0x40010702, 0x40010801,
                             0x40011001, 0x40011101, 0x40011401, 0x40011501, 0x40011503, 0x40011601, 0x40011701,
                             0x40011801, 0x40011901, 0x40012101, 0x40012201, 0x40012301]
        i = 0
        for index, code in enumerate(self.codes):
            code_var = IntVar()
            valu = self.codes_values[index]
            c = Checkbutton(self.code_frame, text=self.codes[index], variable=code_var, onvalue=valu, offvalue=0,
                            command=self.check_codes)
            if i < 5:
                c.select()
            c.pack()
            i = i + 1
            self.decoder.codes_type.append(code_var)
        self.setting_window_btn = Button(self.setting_window, command=self.setting_btn_fun, activebackground='blue',
                                         activeforeground='white', bd=3, bg='cyan', text='确认')
        self.setting_window_btn.place(x=162, y=760, width=self.btn_width, height=self.btn_height, )

        # 照片格式
        self.pic_str = Label(self.setting_window, text='选择图片存储格式:')
        # 下拉框 选择图片格式
        self.pic_type_value = StringVar()
        self.pic_type_combox = ttk.Combobox(self.setting_window, textvariable=self.pic_type_value)
        self.pic_type_combox['values'] = ('jpg', 'bmp', 'png')
        self.pic_type_combox.current(0)
        self.pic_type_combox.bind('<<ComboboxSelected>>', self.set_pic_type)

        # 选择灯光开关
        self.light_on_off_str = Label(self.setting_window, text='光照开关:')
        self.light_on_off = StringVar()
        self.light_on_off_combox = ttk.Combobox(self.setting_window, textvariable=self.light_on_off)
        self.light_on_off_combox['values'] = ('on', 'off')
        self.light_on_off_combox.current(0)
        self.light_on_off_combox.bind('<<ComboboxSelected>>', self.set_light_on_off)

        # 选择光照模式
        self.light_mode_str = Label(self.setting_window, text='光照模式:')
        self.light_mode = StringVar()
        self.light_mode_combox = ttk.Combobox(self.setting_window, textvariable=self.light_mode)
        self.light_mode_combox['values'] = ('Strobe', 'Constant')
        self.light_mode_combox.current(0)
        self.light_mode_combox.bind('<<ComboboxSelected>>', self.set_light_mode)

        # 选择照片像素
        self.ROI_str = Label(self.setting_window, text='设置图片像素:')
        self.ROI_w_h = StringVar()
        # self.ROI_entry = Entry(self.root, textvariable=self.ROI_w_h)
        # self.ROI_btn = Button(self.root, command=self.set_ROI_fun, activebackground='blue',
        #                       activeforeground='white', bd=3,
        #                       bg='cyan', text='确认')
        self.ROI_combox = ttk.Combobox(self.setting_window, textvariable=self.ROI_w_h)
        self.ROI_combox['values'] = ('2592x2048', '1296x1024')
        self.ROI_combox.current(0)
        self.ROI_combox.bind('<<ComboboxSelected>>', self.set_ROI_fun)

        # 设置条码数量
        self.codes_num_str = Label(self.setting_window, text='设置条码数量:')
        self.codes_num = StringVar()
        self.codes_num.set(self.codes_num_value)
        self.codes_num_entry = Entry(self.setting_window, textvariable=self.codes_num)
        self.codes_num_entry.bind('Leave', self.set_codes_num)

    def setting_btn_fun(self):
        print(self.codes_num.get())
        self.codes_num_value = int(self.codes_num.get())
        self.setting_window.withdraw()

    def set_codes_num(self, o):
        print(self.codes_num.get())
        print('sssss')

    def set_ROI_fun(self, o):
        width, height = self.ROI_w_h.get().split('x')
        offsetX = (self.decoder.width - int(width)) // 2
        offsetY = (self.decoder.height - int(height)) //2
        self.cam.set_ROI(int(width), int(height), offsetX, offsetY)

    def setting_config(self):
        self.setting_window.deiconify()

    def set_pic_type(self, arge):
        print(self.pic_type_combox.get())
        self.cam.pic_type = self.pic_type_combox.get()

    def set_light_on_off(self, o):
        state = self.light_on_off.get()
        if state == 'on':
            self.cam.set_light(1)
        else:
            self.cam.set_light(0)

    def set_light_mode(self, o):
        mode = self.light_mode.get()
        if mode == 'Strobe':
            self.cam.set_light_mode(0)
        else:
            self.cam.set_light_mode(1)

    def get_scale_value(self, ev):
        # print(ev)
        if self.light_flag:
            self.light_flag = False
        else:
            self.cam.set_light_flashTime(int(self.scale.get()))
        print(self.scale.get())

    def check_codes(self):
        for var in self.decoder.codes_type:
            if var.get() != 0:
                print(hex(var.get()))

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # self.cam.stop()
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

        self.code_str.place(x=10,y=10)
        self.code_frame.place(x=10, y=30, )
        self.pic_str.place(x=200, y=10)
        self.pic_type_combox.place(x=200, y=30)
        self.light_on_off_str.place(x=200, y=70)
        self.light_on_off_combox.place(x=200, y=90)
        self.light_mode_str.place(x=200, y=130)
        self.light_mode_combox.place(x=200, y=150)
        self.ROI_str.place(x=200, y=190)
        self.ROI_combox.place(x=200, y=210)
        self.codes_num_str.place(x=200, y=250)
        self.codes_num_entry.place(x=200, y=270)

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

    def showResultByPhoto(self):
        self.log_text.config(state=NORMAL)
        self.log_text.delete(0.0, END)
        for idx in range(self.decoder.ResultCount):
            code = self.decoder.ResultList[idx].res_str.value.decode()
            self.write_msg(str(idx) + ':' + code)
        self.log_text.config(state=DISABLED)

    def drawQR(self, bounds):
        x_p = self.canvas_width / self.decoder.width
        y_p = self.canvas_height / self.decoder.height
        for idx, bound in enumerate(bounds):
            code = self.decoder.ResultList[idx].res_str.value.decode()
            self.write_msg(str(idx) + ':' + code)
            # box = self.canvas.create_polygon(int(bound[0][0] * x_p + 140), int(self.canvas_height - bound[0][1] * y_p-5),
            #                                  int(bound[1][0] * x_p + 155), int(self.canvas_height - bound[1][1] * y_p-5),
            #                                  int(bound[2][0] * x_p + 155), int(self.canvas_height - bound[2][1] * y_p+5),
            #                                  int(bound[3][0] * x_p + 140), int(self.canvas_height - bound[3][1] * y_p+5),
            #                                  outline='blue', fill='')
            box = self.canvas.create_polygon(int((bound[0][0]-1080 if bound[0][0]-1080 >= 0 else bound[0][0] + 1512) * x_p - 5),
                                             int(self.canvas_height - bound[0][1] * y_p - 5),
                                             int((bound[1][0]-1080 if bound[1][0]-1080 >= 0 else bound[1][0] + 1512) * x_p + 5),
                                             int(self.canvas_height - bound[1][1] * y_p - 5),
                                             int((bound[2][0]-1080 if bound[2][0]-1080 >= 0 else bound[2][0] + 1512) * x_p + 5),
                                             int(self.canvas_height - bound[2][1] * y_p + 5),
                                             int((bound[3][0]-1080 if bound[3][0]-1080 >= 0 else bound[3][0] + 1512) * x_p - 5),
                                             int(self.canvas_height - bound[3][1] * y_p + 5),
                                             outline='blue', fill='', width=3)
            text = self.canvas.create_text(int((bound[0][0]-1080 if bound[0][0]-1080 >= 0 else bound[0][0] + 1512) * x_p + 150), int(self.canvas_height - bound[0][1] * y_p - 25),
                                           text=code, fill='blue', font=30)
            self.texts.append(text)
            self.boxes.append(box)

    def take_photo_thread(self):
        self.log_text.delete(0.0, 'end')
        self.img_path = self.cam.take_photo()

    def take_photo(self):
        t = threading.Thread(target=self.take_photo_thread)
        t.start()

    def start_cam_thread(self):
        """开启相机，获取实时图像"""
        self.init_cam()
        th = threading.Thread(target=self.cam.real_time_image)
        th.start()
        self.filemenu.insert_command(2, label='停止', command=self.stop_cam)

    def stop_cam(self):
        self.cam.stop()
        self.filemenu.delete(2)

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
            self.exposure_value.set(self.cam.get_exposure_value())
            return True
        except:
            return False

    def reconnection(self):
        self.init_cam()
        self.filemenu.insert_command(2, label='停止', command=self.stop_cam)

    def main(self):
        # 初始化相机
        self.cam = Camera(self)
        # 创建pickle对象
        self.pk = PickleDB()
        file_dir_path = self.pk.get_value_from_key(self.pk.DIR_PATH)
        if file_dir_path != '':
            self.cam.set_photo_path(self.pk.get_value_from_key(self.pk.DIR_PATH))

        self.gui_arrange()
        self.update_canvas()
        mainloop()


qr = QrCode()
qr.gui_arrange()
qr.main()
