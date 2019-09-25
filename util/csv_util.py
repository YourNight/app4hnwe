import csv
import datetime
import os
import sys


class CsvWR:
    def __init__(self, path_parent=sys.path[0]+'\\source\\csv_direction\\', path_prefix='boxdata_'):
        self.path_parent = path_parent
        self.path_prefix = path_prefix
        self.path_suffix = '.csv'

    def create_dir(self):
        isExists = os.path.exists(self.path_parent)

        # 判断结果
        if not isExists:
            # 如果不存在则创建目录
            # 创建目录操作函数
            os.makedirs(self.path_parent)

            print(self.path_parent + ' 创建成功')
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            print(self.path_parent + ' 目录已存在')
            return False

    def set_path_parent(self, path_parent):
        self.path_parent = path_parent + '\\csv_direction\\'
        print(self.path_parent)

    def write_csv(self, msg=['none', 'None']):
        try:
            now_time = datetime.datetime.now().strftime('%Y%m%d')
            # C:\\Users\\18435\\Desktop\\pythonStudy\\
            path = self.path_parent + self.path_prefix + now_time + self.path_suffix
            self.create_dir()
            print('path--->'+path)
            print(sys.path[0])
            out = open(path, 'a', newline='')
            # 设定写入模式
            csv_write = csv.writer(out, dialect='excel')
            # 写入具体内容
            csv_write.writerow(msg)
            return path
        except:
            return False

    @staticmethod
    def format_data(box, bottles):
        result = []
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result.append(now_time)
        result.append(box)
        result.append(tuple(bottles))
        return result
