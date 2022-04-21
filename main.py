# encoding=utf-8
import json
import time
import datetime
import re
import requests
from bs4 import BeautifulSoup as bs
import urllib3

urllib3.disable_warnings()
from encrypt import *


class ImuRooter():

    def __init__(self):
        self.__username = ''
        self.__password = ''

        self.__s = requests.session()
        self.__s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        self.__s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

        self.__https_headers = {
            "Host": "ehall.imu.edu.cn",
            "Referer": "https://ehall.imu.edu.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
        }

    def login(self):
        login_headers = {
            'Host': 'cer.imu.edu.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'
        }
        req = self.__s.get(
            "http://cer.imu.edu.cn/authserver/login?service=https://ehall.imu.edu.cn:443/login?service=https://ehall.imu.edu.cn/ywtb-portal/cusLite/index.html",
            headers=login_headers, verify=False).text
        soup = bs(req, 'lxml')
        login_data = {
            "username": self.__username,
            "password": encodePassword(self.__password,
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
        req2 = self.__s.post(
            'http://cer.imu.edu.cn/authserver/login?service=https://ehall.imu.edu.cn:443/login?service=https://ehall.imu.edu.cn/new/portal/html/message/scenes_message_center.html',
            headers=http_headers, data=login_data, verify=False, allow_redirects=False).text
        soup = bs(req2, 'lxml')
        redirectUrl = soup.a.attrs['href']
        req3 = self.__s.get(redirectUrl, headers=self.__https_headers, verify=False).text
        try:
            req4 = self.__s.get(
                'https://ehall.imu.edu.cn/jsonp/ywtb/info/getUserInfoAndSchoolInfo.json?_=%s' % round(time.time()),
                headers=self.__https_headers, verify=False).json()
        except json.JSONDecodeError:
            print('登录失败')
            return False
        if req4['data']['userName'] != None:
            print('登录成功，欢迎:' + req4['data']['userName'])
            return True
        print('登录失败')
        return False

    def sign(self):
        req5 = self.__s.get(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwStuReportEpidemic/index.do?t_s=%s' % round(time.time()),
            headers=self.__https_headers).text
        info = re.search('USER_INFO=(.*?);', req5).group(1)
        info = json.loads(info)

        wid_data = {
            'pageNumber': "1"
        }
        req6 = self.__s.post(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwStuReportEpidemic/modules/healthClock/getMyTodayReportWid.do',
            headers=self.__https_headers, data=wid_data, verify=False).json()
        l1 = req6['datas']['getMyTodayReportWid']['rows'][0]
        # wid = req6['datas']['getMyTodayReportWid']['rows'][0]['WID']

        wid_data['pageSize'] = 10
        req7 = self.__s.post(
            'https://ehall.imu.edu.cn/qljfwappnew/sys/lwStuReportEpidemic/modules/healthClock/getLatestDailyReportData.do',
            headers=self.__https_headers, data=wid_data).json()
        l2 = req7['datas']['getLatestDailyReportData']['rows'][0]
        l1.update(l2)
        for key in l1.keys():
            if l1[key] == None:
                l1[key] = ''
        appendList = {
            "BY11": "",
            "BY12": "",
            "BY13": "",
            "BY14": "",
            "BY15": "",
            "BY16": "",
            "BY17": "",
            "BY18": "",
            "BY19": "",
            "BY20": "",
            "CLASS_CODE_DISPLAY": info['className'],
            "CLASS_CODE": info['classCode'],
            "MAJOR_CODE_DISPLAY": info['majorName'],
            "MAJOR_CODE": info['majorCode'],
            "FILL_TIME": (datetime.datetime.now() + datetime.timedelta(minutes=-10)).strftime("%Y-%m-%d %H:%M:%S"),
            "CREATED_AT": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        l1.update(appendList)

        postUrl = 'https://ehall.imu.edu.cn/qljfwappnew/sys/lwStuReportEpidemic/modules/healthClock/T_HEALTH_DAILY_INFO_SAVE.do'
        req8 = self.__s.post(postUrl, headers=self.__https_headers, data=l1).json()
        if req8['datas']['T_HEALTH_DAILY_INFO_SAVE'] == 1:
            print('打卡成功')
        else:
            print(req8)


if __name__ == '__main__':
    app=ImuRooter()
    if app.login():
        app.sign()
