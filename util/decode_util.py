import time
from ctypes import *


class ResultEntry:
    def __init__(self):
        self.length = c_int()
        self.res_str = create_string_buffer(100)


class Decode:
    def __init__(self):
        self.RESULT_MAX = 10
        self.ResultCount = 0
        self.ResultList = []
        self.Bounds = []
        # self.dll_path = r'source\SD_x64.dll'
        self.dll_path = r'E:\workspace\vsworkspace\hnwe\SD_x64.dll'
        # self.image_path = r'E:\workspace\c++_workspace\scandit-barcodescanner-windows_5.11.4\CommandLineQrCodeScanner\bin\Debug\1.bmp'
        # self.image_path = ''
        # self.image_path = r'C:\Users\PC\MVS\Data\4.bmp'
        self.sd_dll = windll.LoadLibrary(self.dll_path)

        self.CB_FUNC = WINFUNCTYPE(c_void_p, POINTER(c_int))
        self.width, self.height = 0, 0
        self.c_array = None

        # image = Image.open(self.image_path)
        # self.width, self.height = image.size
        # arr = np.array(image).flatten().tolist()
        # self.c_array = (c_ubyte * len(arr))(*arr)


    def check_SD_set(self, handle, sd_property, value):
        rc = self.sd_dll.SD_Set(handle, sd_property, value)
        if rc == 0:
            print("Set", '%#x' % sd_property, "fail")

    def SD_CB_Result(self, handle):
        length = c_int()
        res_str = create_string_buffer(100)
        # length
        self.sd_dll.SD_Get(handle, c_long(0x40007004), byref(length))
        # string
        self.sd_dll.SD_Get(handle, c_long(0x80007007), byref(res_str))
        re = ResultEntry()
        re.length = length
        re.res_str = res_str
        self.ResultList.append(re)
        self.ResultCount += 1

        bound = ((c_int*2)*4)()
        self.sd_dll.SD_Get(handle, c_long(0x70007001), bound)
        self.Bounds.append(bound)

    def setPros(self, width, height, buffer):
        self.width = width
        self.height = height
        self.c_array = buffer

    def SD_CB_Progress(self, handle):
        if self.ResultCount >= self.RESULT_MAX:
            self.sd_dll.SD_Set(handle, c_long(0x40006001), c_void_p(1))

    def start_decode(self):
        start_time = time.time()
        handle = self.sd_dll.SD_Create()
        handle = c_int(handle)

        # image = Image.open(self.image_path)
        # self.width, self.height = image.size
        # arr = np.array(image).flatten().tolist()
        # self.c_array = (c_ubyte * len(arr))(*arr)

        # print(self.height)
        # height
        self.check_SD_set(handle, c_long(0x40004001), c_void_p(self.height))

        # print(self.width)
        # width
        self.check_SD_set(handle, c_long(0x40004005), c_void_p(self.width))

        # line deta
        self.check_SD_set(handle, c_long(0x40004002), c_void_p(self.width))

        # image pointer
        self.check_SD_set(handle, c_long(0x40004004), (self.c_array))

        # callback result
        cb = self.CB_FUNC(self.SD_CB_Result)
        self.check_SD_set(handle, c_long(0x40003001), cb)

        # progress
        # self.check_SD_set(handle, c_long(0x40003002), self.CB_FUNC(self.SD_CB_Progress))

        # enable qr code
        self.check_SD_set(handle, c_long(0x40010201), c_void_p(1))
        self.check_SD_set(handle, c_long(0x40010301), c_void_p(1))
        self.check_SD_set(handle, c_long(0x40011101), c_void_p(1))
        self.check_SD_set(handle, c_long(0x40011001), c_void_p(1))
        self.check_SD_set(handle, c_long(0x40010901), c_void_p(1))  # qr

        # mirror
        self.check_SD_set(handle, c_long(0x40004003), c_void_p(1))

        # decode
        # sd_dll.SD_Decode.restype = c_int
        # sd_dll.SD_Decode.argtypes = [c_int]
        start_time = time.time()
        result = self.sd_dll.SD_Decode(handle)
        print("Decode result", result)

        if result == 0:
            print("Error =", self.sd_dll.SD_GetLastError())

        # print("SD_Decode Returned: ")
        #
        # if self.ResultCount > 0:
        #     for i in range(self.ResultCount):
        #         print(i, ':', self.ResultList[i].res_str.value.decode())
        #         print('Top Left = ({}, {}) Top Right = ({}, {}) Bottom Right = ({}, {}) Bottom Left = ({}, {})'
        #               .format(self.Bounds[i][0][0], self.Bounds[i][0][1],
        #                       self.Bounds[i][1][0], self.Bounds[i][1][1],
        #                       self.Bounds[i][2][0], self.Bounds[i][2][1],
        #                       self.Bounds[i][3][0], self.Bounds[i][3][1]))
            # for resultEntry in self.ResultList:
            #     print(resultEntry.res_str.value.decode())
        end_time = time.time()
        print("Total time =", end_time - start_time)
        self.sd_dll.SD_Destroy(handle)
        return format(float(end_time - start_time), '0.4f')

    def clearResults(self):
        self.ResultList.clear()

    def clearBounds(self):
        self.Bounds.clear()

    def getResults(self):
        return self.ResultList

    def getBounds(self):
        return self.Bounds

# if __name__ == '__main__':
#     start_time = time.time()
#     for i in range(4):
#         d = Decode()
#         d.image_path = 'C:\\Users\\PC\\MVS\\Data\\' + str(i+1) + '.bmp'
#         d.main()
#         print("SD_Decode Returned: ")
#
#         if d.ResultCount > 0:
#             for i in range(d.ResultCount):
#                 print(i, ':', d.ResultList[i].res_str.value.decode())
#                 print('Top Left = ({}, {}) Top Right = ({}, {}) Bottom Right = ({}, {}) Bottom Left = ({}, {})'
#                       .format(d.Bounds[i][0][0], d.Bounds[i][0][1],
#                               d.Bounds[i][1][0], d.Bounds[i][1][1],
#                               d.Bounds[i][2][0], d.Bounds[i][2][1],
#                               d.Bounds[i][3][0], d.Bounds[i][3][1]))
#         print('***********************************************************************************')
#     end_time = time.time()
#     print("Total time =", end_time - start_time)


