import datetime

import MySQLdb


class Database:

    def __init__(self, host=None, port=None, user=None, password=None, database_name=None, charset='utf8'):
        """

        :rtype: object
        """
        self.host = host  # 127.0.0.1
        self.port = port  # 3306
        self.user = user  # my_test
        self.password = password  # 123456
        self.database_name = database_name  # my_test
        self.charset = charset  # utf-8
        self.mysql_db = None
        self.cursor = None

    def get_connect(self):
        try:
            if self.mysql_db is None:
                self.mysql_db = MySQLdb.connect(host=self.host,
                                                port=self.port,
                                                user=self.user,
                                                password=self.password,
                                                database=self.database_name,
                                                charset='utf8')
                self.cursor = self.mysql_db.cursor()
                return True
        except:
            return False

    def execute_update(self, sql):
        try:
            # 执行SQL语句
            ret = self.cursor.execute(sql)
            # 提交修改
            self.mysql_db.commit()
            return ret
        except:
            # 发生错误时回滚
            self.mysql_db.rollback()

    def execute_select(self, sql):
        try:
            # 执行SQL语句
            self.cursor.execute(sql)
            # 获取所有记录列表
            results = self.cursor.fetchall()
            return results
        except:
            print("Error: unable to fecth data")
            return ''

    def close_connect(self):
        if self.mysql_db is not None:
            self.mysql_db.close()

    @staticmethod
    def add_sql(box, bottles):
        sql = 'INSERT INTO BOX_BOTTLE(BOTTLE_VALUE,BOX_VALUE,TIME) VALUES '
        for i in range(len(bottles)):
            now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            sql = sql + "('" + str(bottles[i]) + "','" + str(box) + "','" + str(now_time) + "')"
            if i < len(bottles) - 1:
                sql = sql + ','
        return sql

    @staticmethod
    def format_results(results):
        result_list = []
        length = len(results)
        for i in range(length):
            resule = results[i]
            result_map = {}
            result_map['bottle_value'] = resule[1]
