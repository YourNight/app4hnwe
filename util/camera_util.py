# coding: utf-8
import base64
import datetime
import time
from tkinter import messagebox

import math
import os
import random
import sys
from io import BytesIO
import numpy as np
from PIL import Image

from mvImport.MvCameraControl_class import *



class Camera:
    def __init__(self, qr_code, photo_path=sys.path[0]+'\\source\\picture_direction\\'):
        self.exposure_time = 0
        self.deviceList = MV_CC_DEVICE_INFO_LIST() #设备列表
        self.tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE #设备型号
        self.cam = None
        self.nPayloadSize = None
        self.photo_path = photo_path
        # self.create_dir()
        self.qr_code = qr_code

        # print(self.exposureTime)

    def create_dir(self):
        isExists = os.path.exists(self.photo_path)

        # 判断结果
        if not isExists:
            # 如果不存在则创建目录
            # 创建目录操作函数
            os.makedirs(self.photo_path)

            print(self.photo_path + ' 创建成功')
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            print(self.photo_path + ' 目录已存在')
            return False

    def set_photo_path(self, photo_path):
        self.photo_path = photo_path+'\\picture_direction\\'
        # self.create_dir()
        print(self.photo_path)

    def connect_camera_by_enum(self, nConnectionNum=0):
        if int(nConnectionNum) >= self.deviceList.nDeviceNum:
            print("ConnectionNum error!")
            return False
        else:
            # ch:创建相机实例 | en:Creat Camera Object
            self.cam = MvCamera()

            # ch:选择设备并创建句柄 | en:Select device and create handle
            stDeviceList = cast(self.deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

            ret = self.cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                print("create handle fail! ret[0x%x]" % ret)
                return False
            else:
                # ch:打开设备 | en:Open device
                ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
                if ret != 0:
                    print("open device fail! ret[0x%x]" % ret)
                    return False
                else:
                    # ch:探测网络最佳包大小(只对GigE相机有效) |
                    # en:Detection network optimal package size(It only works for the GigE camera)
                    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                        nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
                        if int(nPacketSize) > 0:
                            ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                            if ret != 0:
                                print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
                        else:
                            print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)
                    # 曝光
                    value = MV_EXPOSURE_AUTO_MODE_OFF
                    ret = self.cam.MV_CC_SetEnumValue('ExposureMode', value)
                    # if ret != 0:
                    #     print('set exposure mode fail')
                    # else:
                    #     ret = self.cam.MV_CC_SetFloatValue('ExposureTime', self.exposure_time)
                    #     if ret != 0:
                    #         print('set exposure time fail')
                    #     else:
                    #         print('set exposure time:' + str(self.exposure_time))
                            # self.cam.MV_CC_GetFloatValue('ExposureTime', MVCC_FLOATVALUE)
                            # print(MVCC_FLOATVALUE)

                    # ch:设置触发模式为off | en:Set trigger mode as off
                    ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
                    if ret != 0:
                        print("set trigger mode fail! ret[0x%x]" % ret)
                        return False
                    else:
                        return True

    def set_exposure_value(self):

        ret = self.cam.MV_CC_SetFloatValue('ExposureTime', float(self.exposure_time))
        if ret != 0:
            print('set exposure time fail')
        else:
            print('set exposure time:' + str(self.exposure_time))

    def get_exposure_value(self):
        f = c_float()
        ret = self.cam.MV_CC_GetFloatValue('ExposureTime', f)
        if ret != 0:
            print('get exposure time fail')
        else:
            print('exposure time:' + str(f))
            self.exposure_time = f.value
        return self.exposure_time

    def getIP(self):
        ip = c_int()
        ret = self.cam.MV_CC_GetIntValue('GevPersistentIPAddress', ip)
        if ret != 0:
            print('get ip fail')
        else:
            print('ip:' + str(ip))


    def start_grabbing(self):
        # ch:获取数据包大小 | en:Get payload size
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
        ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
        if ret != 0:
            print("get payload size fail! ret[0x%x]" % ret)
        else:
            self.nPayloadSize = stParam.nCurValue
            # ch:开始取流 | en:Start grab image
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                print("start grabbing fail! ret[0x%x]" % ret)
                return False
            else:
                return True

    def real_time_image(self):
        stDeviceList = MV_FRAME_OUT_INFO_EX()
        memset(byref(stDeviceList), 0, sizeof(stDeviceList))
        try:
            data_buf = (c_ubyte * self.nPayloadSize)()
        except:
            messagebox.showwarning(title='警告！', message='启动失败，请确认相机是否连接成功！')
        while True:
            ret = self.cam.MV_CC_GetOneFrameTimeout(byref(data_buf), self.nPayloadSize, stDeviceList, 1000)
            if ret == 0:
                # nRGBSize = stDeviceList.nWidth * stDeviceList.nHeight * 3
                nRGBSize = (stDeviceList.nWidth * stDeviceList.nHeight * 3) + 2048
                stConvertParam = MV_SAVE_IMAGE_PARAM_EX()
                stConvertParam.nWidth = stDeviceList.nWidth
                stConvertParam.nHeight = stDeviceList.nHeight
                stConvertParam.pData = data_buf
                stConvertParam.nDataLen = stDeviceList.nFrameLen
                stConvertParam.enPixelType = stDeviceList.enPixelType
                stConvertParam.nJpgQuality = 70

                # stConvertParam.enImageType = MV_Image_Jpeg
                stConvertParam.enImageType = MV_Image_Bmp
                stConvertParam.pImageBuffer = (c_ubyte * nRGBSize)()
                stConvertParam.nBufferSize = nRGBSize
                ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
                # ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
                if ret != 0:
                    print("convert pixel fail! ret[0x%x]" % ret)
                    del data_buf
                else:
                    img_buff = (c_ubyte * stConvertParam.nImageLen)()
                    cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pImageBuffer,
                                       stConvertParam.nImageLen)
                    arr = np.asarray(img_buff)
                    f = BytesIO(arr)
                    image = Image.open(f)
                    # print(image)
                    if image.mode not in ('L', 'RGB'):
                        image = image.convert('RGB')
                    # print(img_buff)
                    self.qr_code.update_canvas_from_cam(image)
                    if self.qr_code.decode_flag:
                        print('start=========================================')
                        if self.qr_code.boxes:
                            self.qr_code.canvas.delete(self.qr_code.boxes)
                        if self.qr_code.texts:
                            self.qr_code.canvas.delete(self.qr_code.texts)
                        # 霍尼韦尔解码
                        self.qr_code.decoder.setPros(stDeviceList.nWidth, stDeviceList.nHeight, img_buff)
                        decode_time = self.qr_code.decoder.start_decode()
                        self.qr_code.show_decode_time(decode_time)
                        print(self.qr_code.decoder.ResultCount)
                        if self.qr_code.decoder.ResultCount > 0:
                            self.qr_code.drawQR(self.qr_code.decoder.Bounds)
                            for i in range(self.qr_code.decoder.ResultCount):
                                print(i, ':', self.qr_code.decoder.ResultList[i].res_str.value.decode())
                                print(
                                    'Top Left = ({}, {}) Top Right = ({}, {}) Bottom Right = ({}, {}) Bottom Left = ({}, {})'
                                        .format(self.qr_code.decoder.Bounds[i][0][0], self.qr_code.decoder.Bounds[i][0][1],
                                                self.qr_code.decoder.Bounds[i][1][0], self.qr_code.decoder.Bounds[i][1][1],
                                                self.qr_code.decoder.Bounds[i][2][0], self.qr_code.decoder.Bounds[i][2][1],
                                                self.qr_code.decoder.Bounds[i][3][0], self.qr_code.decoder.Bounds[i][3][1]))
                        print('***********************************************************************************')
                        self.qr_code.decoder.clearResults()
                        self.qr_code.decoder.clearBounds()
                        self.qr_code.decoder.ResultCount = 0

    def take_photo(self):
        stDeviceList = MV_FRAME_OUT_INFO_EX()
        memset(byref(stDeviceList), 0, sizeof(stDeviceList))
        try:
            data_buf = (c_ubyte * self.nPayloadSize)()
        except:
            messagebox.showwarning(title='警告！', message='启动失败，请确认相机是否连接成功！')
        ret = self.cam.MV_CC_GetOneFrameTimeout(byref(data_buf), self.nPayloadSize, stDeviceList, 1000)
        if ret == 0:
            print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (
                stDeviceList.nWidth, stDeviceList.nHeight, stDeviceList.nFrameNum))

            # nRGBSize = stDeviceList.nWidth * stDeviceList.nHeight * 3
            nRGBSize = (stDeviceList.nWidth * stDeviceList.nHeight * 3) + 2048
            stConvertParam = MV_SAVE_IMAGE_PARAM_EX()
            stConvertParam.nWidth = stDeviceList.nWidth
            stConvertParam.nHeight = stDeviceList.nHeight
            stConvertParam.pData = data_buf
            stConvertParam.nDataLen = stDeviceList.nFrameLen
            stConvertParam.enPixelType = stDeviceList.enPixelType
            stConvertParam.nJpgQuality = 70

            # stConvertParam.enImageType = MV_Image_Jpeg
            stConvertParam.enImageType = MV_Image_Bmp
            stConvertParam.pImageBuffer = (c_ubyte * nRGBSize)()
            stConvertParam.nBufferSize = nRGBSize
            # ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
            ret = self.cam.MV_CC_SaveImageEx2(stConvertParam)
            if ret != 0:
                print("convert pixel fail! ret[0x%x]" % ret)
                del data_buf
            else:
                now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                rannum = random.randint(0, 1000)
                self.create_dir()
                file_path = self.photo_path+"picture"+now_time+"_"+str(rannum)+".jpg"
                file_open = open(file_path.encode('ascii'), 'wb+')
                img_buff = (c_ubyte * stConvertParam.nImageLen)()
                cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pImageBuffer,
                                   stConvertParam.nImageLen)
                print('start=========================================')
                if self.qr_code.boxes:
                    self.qr_code.canvas.delete(self.qr_code.boxes)
                if self.qr_code.texts:
                    self.qr_code.canvas.delete(self.qr_code.texts)
                # 霍尼韦尔解码
                self.qr_code.decoder.setPros(stDeviceList.nWidth, stDeviceList.nHeight, img_buff)
                decode_time = self.qr_code.decoder.start_decode()
                self.qr_code.show_decode_time(decode_time)
                print(self.qr_code.decoder.ResultCount)
                if self.qr_code.decoder.ResultCount > 0:
                    self.qr_code.drawQR(self.qr_code.decoder.Bounds)
                    for i in range(self.qr_code.decoder.ResultCount):
                        print(i, ':', self.qr_code.decoder.ResultList[i].res_str.value.decode())
                        print('Top Left = ({}, {}) Top Right = ({}, {}) Bottom Right = ({}, {}) Bottom Left = ({}, {})'
                              .format(self.qr_code.decoder.Bounds[i][0][0], self.qr_code.decoder.Bounds[i][0][1],
                                      self.qr_code.decoder.Bounds[i][1][0], self.qr_code.decoder.Bounds[i][1][1],
                                      self.qr_code.decoder.Bounds[i][2][0], self.qr_code.decoder.Bounds[i][2][1],
                                      self.qr_code.decoder.Bounds[i][3][0], self.qr_code.decoder.Bounds[i][3][1]))
                print('***********************************************************************************')
                self.qr_code.decoder.clearResults()
                self.qr_code.decoder.clearBounds()
                self.qr_code.decoder.ResultCount = 0
                file_open.write(img_buff)
            print("Save Image succeed!")
            return file_path

    def get_device(self):
        # ch:枚举设备 | en:Enum device
        ret = MvCamera.MV_CC_EnumDevices(self.tlayerType, self.deviceList)
        if ret != 0:
            print("enum devices fail! ret[0x%x]" % ret)
            return False

        if self.deviceList.nDeviceNum == 0:
            print("find no device!")
            return False

        print("find %d devices!" % self.deviceList.nDeviceNum)
        return True

    def show_all_device(self):
        for i in range(0, self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print("\ngige device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)

    def stop(self):
        # ch:停止取流 | en:Stop grab image
        ret = self.cam.MV_CC_StopGrabbing()
        if ret != 0:
            print("stop grabbing fail! ret[0x%x]" % ret)

        # ch:关闭设备 | Close device
        ret = self.cam.MV_CC_CloseDevice()
        if ret != 0:
            print("close deivce fail! ret[0x%x]" % ret)

        # ch:销毁句柄 | Destroy handle
        ret = self.cam.MV_CC_DestroyHandle()
        if ret != 0:
            print("destroy handle fail! ret[0x%x]" % ret)

