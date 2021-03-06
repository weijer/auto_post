#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 自动发帖主程序

from sys import argv
from platform import system
import time

from module.database.user import User
from module.database.house_info import HouseInfoXlsx, HouseInfo
from module.sele.send_house import SendHouse
from module.database.house_search import HouseSearch
from module.xlsx.house_list_finder import HouseListFinder
from module.xlsx.config_reader import ConfigReader

from constant.logger import unknown, base_info, base_warn, base_err, base_fatal
from constant.dict import *

def user_cmd(opt_id, username=""):
    '''用户信息操作命令'''
    user = User()
    opt = user_cmd_dict[str(opt_id)]

    try:
        if opt_id == 3:
            pwd = user.get_user_password(username)
            print("用户【%s】的信息如下\n密码：%s\n用户类型：%s"%(pwd[0],pwd[1],user_type_dict[str(pwd[2])]))
        elif opt_id == 4:
            print("当前查询到的用户名有...\n\n%s\n"%"\n".join([user[0] for user in user.all_users]))
        else:
            password = input("请输入用户[%s]进行%s操作的密码\n"%(username, opt))
            usertype = int(input("请输入需要%s操作的用户类型 1-只有安居客 2-既有安居客又有58同城\n"%opt))
            if usertype not in [1, 2]:
                raise ValueError("用户类型错误！")

            if opt_id == 1:
                '''新增'''
                user.insert_user(username, password, usertype)
            elif opt_id == 2:
                '''修改'''
                user.update_user(username, password, usertype)
            else:
                raise ValueError("没有这个操作")
    except Exception as e:
        base_err(str(e))
    finally:
        user.close

def send_cmd(username):
    '''通过cmd发帖'''
    user = User()
    is_exist = user.user_exist(username)
    if not is_exist:
        base_warn("没有找到用户名为[%s]的用户，继续操作将为您新增此用户..."%username)
        user_cmd(1, username)
    else:
        run = True
        hs_list = list()
        size_list = list()
        store_list = list()
        while True:
            while run:
                store = input("请输入需要推广的门店名称")
                store_list.append(store)
                try:
                    size = int(input("请输入需要推广的数量"))
                    size_list.append(size)
                    housetype = int(input("请输入房源类型（几室）"))
                    source = int(input("请输入房源来源（1-推广 2-本地 3-集中式 4-第三方）"))
                    if source not in [1, 2, 3]:
                        raise ValueError("类型错误！")
                except Exception as e:
                    base_warn("推广数量、房源类型、房源来源请输入数字！ Err:%s"%str(e))
                else:
                    break
            base_info("筛选房源中...")
            hs_list.append(HouseSearch(store, size, housetype, source).house_list)
            if input("是否继续添加房源？(Y/N)") == "Y":
                run = True
            else:
                run = False
                break
        send_house_proc(hs_list, size_list, store_list)

def send_config(username):
    '''通过配置文件发帖'''
    user = User()
    hs_list = list()
    is_exist = user.user_exist
    if not is_exist:
        base_warn("没有找到用户名为[%s]的用户，继续操作将为您新增此用户..."%username)
        user_cmd(1, username)
    else:
        order_reader = ConfigReader("/data/config/发帖配额.xlsx")
        order_list = order_reader.order_list
        for order in order_list:
            hs_list.append(HouseSearch(order[0], order[1], order[2], order[3]).house_list)
        send_house_proc(hs_list, order_reader.size_list, order_reader.store_list)
        

def send_house_proc(hs_list, size_list, store_list):
    '''房源发送进程（并没有使用多进程）'''
    base_info("用户[%s]开始尝试登录..."%username)
    for size, store in zip(size_list, store_list):
        base_info("准备发送门店[%s]的[%s]套房源"%(store, size))
    
    time.sleep(5)

    sender_base = SendHouse(username,[],None)
    for idx in range(0, len(hs_list)):
        sender = SendHouse(username, hs_list[idx], sender_base.browser)
        send_house = sender.send
        send_count = 0

        while True:
            try:
                send = next(send_house)
                if send:
                    send_count = send_count + 1
                if send_count >= size_list[idx]:
                    raise RuntimeError("房源发送完毕多余房源停止发送")
            except SystemExit:
                sender.browser.quit()
                raise
            except Exception:
                if idx == len(hs_list) - 1:
                    base_info("所有房源发送完毕！") 
                    sender.browser.quit()
                break

        base_info("[%s]房源发送结束！共发布成功[%d]套房源"%(store_list[idx], send_count))


if __name__ == '__main__':

    if len(argv) == 1:
        username = input("请输入需要登录的用户名\n")
        send_config(username)
    
    # 带参数的执行程序
    if len(argv) == 2:
        # 用户信息维护操作
        if argv[1].strip() == "user":
            base_info("开始用户信息维护操作")
            while True:
                opt_id = int(input("请输入需要进行的用户操作：\n【0】退出程序\n【1】新增用户\n【2】修改用户\n【3】查看用户\n【4】查询所有用户名\n"))
                if opt_id > 0 and opt_id <= 3:
                    username = input("请输入需要操作的用户名\n")
                    user_cmd(opt_id, username)
                elif opt_id == 4:
                    user_cmd(opt_id)
                elif opt_id == 0:
                    base_info("用户信息维护程序退出...")
                    break
                else:
                    base_warn("没有这个操作【%d】"%opt_id)
                    pass

        # 数据导入操作
        elif argv[1].strip() == "import":
            try:
                clean = HouseInfo().truncate_house_info
                base_info("开始数据导入操作")
                base_info("自动发帖运行在系统是%s的机器上..."%system())
                if system() == "Linux":
                    finder = HouseListFinder().house_file_list
                    for find in finder:
                        x = HouseInfoXlsx(find)
                        x.insert_data
                elif system() == "Windows":
                    x = HouseInfoXlsx(r"C:\\Users\\Administrator\\Documents\\auto_post\\house_list.xlsx")
                    x.insert_data
            except FileNotFoundError:
                base_fatal("没有找到房源信息文件！请检查！")
            except Exception as e:
                unknown(str(e))
        
        # 发送操作
        elif argv[1].strip() == "send":
            username = input("请输入需要登录的用户名\n")
            send_cmd(username)

        # 通过配置文件发送操作
        elif argv[1].strip() == "start":
            username = input("请输入需要登录的用户名\n")
            send_config(username)
        
    elif len(argv) == 3:

        if argv[1].strip() == "start":
            username = argv[2].strip()
            send_config(username)
