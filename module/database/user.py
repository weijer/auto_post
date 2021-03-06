# 用户表操作
from util.database import DBController
from util.common.logger import use_logger
from constant.logger import db_err

class User(DBController):

    def __init__(self):
        DBController.__init__(self)

    def get_user_password(self, username):
        '''通过用户名获取用户密码'''
        from .sql_template import get_user_password_sql

        sql_execute = get_user_password_sql.format(username=username)
        
        self.execute(sql_execute)
        rtn = self.cur.fetchone()

        if rtn is not None:
            return rtn
        else:
            raise ValueError("数据表中没有这个用户！")

    def insert_user(self, username, password, usertype, name=""):
        '''向表中插入一条数据'''
        from .sql_template import insert_user_sql

        sql_execute = insert_user_sql.format(username=username, password=password,\
        usertype=usertype, name=name)

        try:
            self.execute(sql_execute)
        except Exception as e:
            db_err("向用户表中插入一条数据失败！ e:%s, SQL: %s"%(str(e),sql_execute))

    def user_exist(self, username):
        '''查询某一用户在数据表中是否存在 返回布尔值'''
        try:
            rtn = self.get_user_password(username)
        except ValueError:
            return False
        return True
    
    def update_user(self, username, password, usertype, name=""):
        '''更新某一用户的账户信息'''
        from .sql_template import update_user_sql

        sql_execute = update_user_sql.format(username=username, password=password,\
        usertype=usertype, name=name)

        try:
            self.execute(sql_execute)
        except Exception:
            db_err("修改用户表中【{username}】信息错误！".format(user_name=username))

    @property
    def all_users(self):
        '''查询当前数据表中所有的用户列表'''
        sql_execute = "select username from auto_post_users"

        try:
            self.execute(sql_execute)
            usernames = self.cur.fetchall()
        except Exception:
            db_err("查询用户表中所有用户列表失败！")
        return usernames

    @property
    def close(self):
        DBController.close