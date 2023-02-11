# encoding=utf-8
import configparser
import json
import time
import datetime
import re
import requests
from bs4 import BeautifulSoup as bs
import urllib3
import random

urllib3.disable_warnings()
from encrypt import *
from logger import logger

class ImuEhall():
    def __init__(self,username,password,send_url):
        if username!=None and password !=None:
            self.__username = username
            self.__password = password
            self.__send_url = send_url
        else:
            self.__parse_config()

        self.__send_msg = ''
        self.__s = requests.session()
        self.__s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        self.__s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        self.__https_headers = {
            "Host": "ehall.imu.edu.cn",
            "Referer": "https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
        }

    def login(self):
        if self.__username=='' or self.__password=='':
            logger.error("缺少必要的登录参数")
            return False
        login_headers = {
            'Host': 'cer.imu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'
        }
        # 先访问一次获取cookie
        req = self.__s.get(
            "http://cer.imu.edu.cn/authserver/login?service=https://ehall.imu.edu.cn:443/login?service=https://ehall.imu.edu.cn/ywtb-portal/cusLite/index.html",
            headers=login_headers, verify=False).text
        soup = bs(req, 'lxml')
        login_data = {
            "username": self.__username,
            "password": encode_password(self.__password,
                                       soup.find(attrs={'id': 'pwdDefaultEncryptSalt'}).attrs['value']),
            "lt": soup.find(attrs={'name': 'lt'}).attrs['value'],
            "dllt": soup.find(attrs={'name': 'dllt'}).attrs['value'],
            "execution": soup.find(attrs={'name': 'execution'}).attrs['value'],
            "_eventId": "submit",
            "rmShown": "1"
        }
        http_headers = {
            "Host": "cer.imu.edu.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Origin": "http://cer.imu.edu.cn",
            "Referer": "http://cer.imu.edu.cn/",
        }
        #正式登录请求
        req2 = self.__s.post(
            'http://cer.imu.edu.cn/authserver/login?service=https://ehall.imu.edu.cn:443/login?service=https://ehall.imu.edu.cn/new/portal/html/message/scenes_message_center.html',
            headers=http_headers, data=login_data, verify=False, allow_redirects=False).text
        soup = bs(req2, 'lxml')
        login_res=soup.find(attrs={"class","auth_error"})
        if login_res:
            logger.error(login_res.text)
            self.__send_msg += login_res.text+'\n\n'
            return False
        redirectUrl = soup.a.attrs['href']
        #获取cookie
        req3 = self.__s.get(redirectUrl, headers=self.__https_headers, verify=False).text
        #判断是否登录成功
        try:
            req4 = self.__s.get(
                'https://ehall.imu.edu.cn/jsonp/ywtb/info/getUserInfoAndSchoolInfo.json?_=%s' % round(time.time()),
                headers=self.__https_headers, verify=False).json()
        except json.JSONDecodeError:
            logger.error('登录失败')
            self.__send_msg+='登录失败\n\n'
            return False
        if req4['data']['userName'] != None:
            logger.info('登录成功，欢迎:' + req4['data']['userName'])
            self.__send_msg+='登录成功\n\n'
            return True
        logger.error('登录失败')
        self.__send_msg += '登录失败\n\n'
        return False

    #签到
    def sign(self):
        #获取个人信息
        req5 = self.__s.get(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/index.do?t_s=%s' % round(time.time()),
            headers=self.__https_headers).text
        info = re.search('USER_INFO=(.*?);', req5).group(1)
        info = json.loads(info)

        origin_data = {
            'pageNumber': "1"
        }
        # 获取住宿信息
        req9 = self.__s.post(
            "https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/modules/healthClock/getSelfZsData.do",headers=self.__https_headers,data=origin_data).json()
        zsData=req9['datas']['getSelfZsData']['rows'][0]
        #判断是否打卡
        check = self.__s.post(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/modules/healthClock/getTodayHasReported.do',
            headers=self.__https_headers,data=origin_data).json()
        if check['datas']['getTodayHasReported']['totalSize']!=0:
            logger.info('之前已打卡')
            self.__send_msg+='之前已打卡\n\n'
            return
        #获取表单
        req6 = self.__s.post(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/modules/healthClock/getMyTodayReportWid.do',
            headers=self.__https_headers, data=origin_data, verify=False).json()
        l1 = req6['datas']['getMyTodayReportWid']['rows'][0]
        # wid = req6['datas']['getMyTodayReportWid']['rows'][0]['WID']

        origin_data['pageSize'] = 10
        #获取最新保存表单
        req7 = self.__s.post(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/modules/healthClock/getLatestDailyReportData.do',
            headers=self.__https_headers, data=origin_data).json()
        l2 = req7['datas']['getLatestDailyReportData']['rows'][0]
        l1.update(l2)
        for key in l1.keys():
            if l1[key] == None:
                l1[key] = ''
        #增加缺失项
        appendList={
            "CLASS_CODE_DISPLAY": info['className'],
            "CLASS_CODE": info['classCode'],
            "MAJOR_CODE_DISPLAY": info['majorName'],
            "MAJOR_CODE": info['majorCode'],
            "GENDER_CODE_DISPLAY":info['gender'],
            "GENDER_CODE":info['genderCode'],
            "CAMPUS":zsData['XQMC'],
            "DORMITORY":zsData['SSLMC'],
            "ROOM_NO":zsData['FJH'],
            "FILL_TIME": (datetime.datetime.now() + datetime.timedelta(seconds=random.randint(-600, -60))).strftime(
                "%Y-%m-%d %H:%M:%S"),
            "CREATED_AT": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        l1.update(appendList)

        postUrl = 'https://ehall.imu.edu.cn/qljfwappnew/sys/lwImuReportEpidemic/modules/healthClock/T_STU_DAILY_INFO_SAVE.do'
        #post表单
        req8 = self.__s.post(postUrl, headers=self.__https_headers, data=l1).json()
        if req8['datas']['T_STU_DAILY_INFO_SAVE'] == 1:
            logger.info('打卡成功')
            self.__send_msg += '打卡成功\n\n'
        else:
            logger.error(req8)
            self.__send_msg += '打卡失败，请查看日志\n\n'

    def send_to_server(self):
        # server酱发送模块
        if self.__send_url == "" or self.__send_msg=='':
            return
        data = {
            'title': "imuEhall",
            'desp': self.__send_msg
        }
        requests.post(self.__send_url,data=data)

    def __parse_config(self):
        cf = configparser.ConfigParser()
        cf.read('config.ini', encoding="utf-8-sig")
        self.__username = cf.get("login", "username")
        self.__password = cf.get("login", "password")
        self.__send_url = cf.get("server", "url")