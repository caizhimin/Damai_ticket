import json
import random
import requests
import os
import base64
import urllib3
import time
import pandas as pd
import re
import pickle
from pandas import DataFrame
from common import print_with_time
from a_js_crack import cookie_crack

urllib3.disable_warnings()
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)
# pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)


class Ticket:
    def __init__(self, phone, buy=0):
        self.session = requests.session()
        self.lock_seats = None
        self.ticketSeatParams = None
        self.cookies_dir_path = "%s/access_token/" % os.path.abspath(os.path.dirname(__file__))
        self.seat_info = ''
        self.headers = {}
        self.buy = buy
        self.one2oneAudiences = []
        # cookie_crack(self.session)
        online_result = self.check_online_login(phone=phone)
        if not online_result:
            local_result = self.check_local_login(phone=phone)
            if not local_result:
                print('%s 在线和本地登录均失效' % phone)
            elif buy:
                print_with_time('%s 本地登录成功' % phone)
        elif buy:
            print_with_time('%s 在线登录成功' % phone)

    def get_address(self):
        address_url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user/addresses/default?merchantId=6267a80eed218542786f1494&ver=3.1.9&channelId=&src=weixin_mini&appId=wxad60dd8123a62329'
        r = self.session.get(url=address_url, verify=False).json()
        print_with_time('address %s' % r)
        return r

    def get_audiences(self, amount=None, bizShowSessionId=None):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/buyer/v1/user_audiences'
        data = {'offset': 0,
                'length': 500,
                'idTypes': '',
                'showId': '',
                "merchantId": "6267a80eed218542786f1494",
                "ver": "3.7.2",
                "src": "weixin_mini",
                "appId": "wxad60dd8123a62329"
                }
        res = self.session.get(url, params=data, verify=False).json()
        tmp = []
        for i in res.get('data'):
            print(i.get('id'))
            print(i.get('idNo'))
            print(i.get('name'))
            print('---------------')
            tmp.append(i.get('id'))
        if amount and bizShowSessionId:
            for i in tmp[0:amount]:
                self.one2oneAudiences.append({"audienceId": i, "sessionId": bizShowSessionId})
        return tmp

    def get_audiences_dict(self):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/buyer/v1/user_audiences'
        data = {'offset': 0,
                'length': 500,
                'idTypes': '',
                'showId': '',
                "merchantId": "6267a80eed218542786f1494",
                "ver": "3.7.2",
                "src": "weixin_mini",
                "appId": "wxad60dd8123a62329"
                }
        res = self.session.get(url, params=data, verify=False).json()

        tmp = []
        for i in res.get('data'):
            idNo = i.get('idNo')
            name = i.get('name')
            tmp.append({'name': name, 'idNo': idNo})
        return tmp

    def generate_photo_code(self, phone):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/generate_photo_code'
        data = {
            "cellphone": "%s" % phone,
            "verifyCodeUseType": "USER_LOGIN",
            "messageType": "MOBILE",
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.7.2",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329"
        }
        headers = {
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.16(0x18001042) NetType/WIFI Language/zh_CN",
            "Accept-Encoding": "gzip, deflate, br",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "merchant-id": "6267a80eed218542786f1494",
            "ver": "3.7.2",
            "Content-Type": "application/json",
            # "access-token": access_token,
        }
        res = self.session.post(url, json=data, headers=headers, verify=False).json()
        baseCode = res.get('data').get('baseCode')[22:]
        # print(baseCode)
        img_data = base64.b64decode(baseCode)
        # print_with_time(img_data)
        with open('captcha.jpg', 'wb') as fw:
            fw.write(img_data)

    def sms_login(self, phone, openid):
        send_verify_code_url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/pub/v3/send_verify_code'
        send_verify_code_data = {
            "verifyCodeUseType": "USER_LOGIN",
            "cellphone": "%s" % phone,
            "messageType": "MOBILE",
            "token": "",
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.7.2",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329"
        }
        send_verify_code_res = self.session.post(send_verify_code_url, json=send_verify_code_data, verify=False).json()
        if (send_verify_code_res.get('comments') == '请先输入图形验证码') or (
                send_verify_code_res.get('comments') == '请刷新图形验证码'):
            self.generate_photo_code(phone)
            photo_code = input('请输入图形验证码')
            # send_verify_code_url = 'https://6267a80eed218542786f1494.m.piaoxingqiu.com/cyy_buyerapi/pub/v2/send_verify_code'
            # send_verify_code_url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v2/send_verify_code'
            send_verify_code_url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/pub/v3/send_verify_code'
            send_verify_code_data = {
                "verifyCodeUseType": "USER_LOGIN",
                "cellphone": "%s" % phone,
                "messageType": "MOBILE",
                "token": "%s" % photo_code,
                "merchantId": "6267a80eed218542786f1494",
                "ver": "3.7.2",
                "channelId": "",
                "src": "weixin_mini",
                "appId": "wxad60dd8123a62329"
            }
            send_verify_code_res = self.session.post(send_verify_code_url, json=send_verify_code_data,
                                                     verify=False).json()

            # url = 'https://6267a80eed218542786f1494.m.piaoxingqiu.com/cyy_buyerapi/pub/v1/wx//mini/cellphone_login_or_register'
            # url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/wx//mini/cellphone_login_or_register'
            url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/pub/v3/wx/mini/cellphone_login_or_register'
            verifyCode = input('请输入短信验证码')
            data = {
                "cellphone": "%s" % phone,
                "verifyCode": "%s" % verifyCode,
                "unionId": None,
                "openId": "%s" % openid,
                "appId": "wxad60dd8123a62329",
                "merchantId": "6267a80eed218542786f1494",
                "ver": "3.7.2",
                "channelId": "",
                "src": "weixin_mini"
            }
            res = self.session.post(url, json=data, verify=False).json()
            # print_with_time(res)
            # accessToken = res.get('data').get('accessToken')
            accessToken = res.get('data').get('refreshToken')
            print('accessToken', accessToken)
            cookies_file = '{}{}.txt'.format(self.cookies_dir_path, phone)
            print('cookies_file', cookies_file)
            directory = os.path.dirname(cookies_file)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(cookies_file, 'w') as f:
                f.write(accessToken)
                f.close()
        else:
            # url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/wx//mini/cellphone_login_or_register'
            url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/pub/v3/wx/mini/cellphone_login_or_register'
            verifyCode = input('请输入短信验证码')
            data = {
                "cellphone": "%s" % phone,
                "verifyCode": "%s" % verifyCode,
                "unionId": None,
                "openId": "%s" % openid,
                "appId": "wxad60dd8123a62329",
                "merchantId": "6267a80eed218542786f1494",
                "ver": "3.7.2",
                "channelId": "",
                "src": "weixin_mini"
            }
            res = self.session.post(url, json=data, verify=False).json()
            print_with_time(res)
            # accessToken = res.get('data').get('accessToken')
            accessToken = res.get('data').get('refreshToken')
            cookies_file = '{}{}.txt'.format(self.cookies_dir_path, phone)
            directory = os.path.dirname(cookies_file)
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(cookies_file, 'w') as f:
                f.write(accessToken)
                f.close()

    def check_online_login(self, phone):
        try:
            url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/profile?merchantId=6267a80eed218542786f1494&ver=3.1.9&channelId=&src=weixin_mini&appId=wxad60dd8123a62329'
            csv_df = pd.read_csv(os.path.abspath(os.path.dirname(__file__)) + '/a_pay_app_pxq_account_info.csv')

            phone_df = csv_df.loc[csv_df['account'] == int(phone)]
            access_token = phone_df.iloc[0]['access_token']
            openid = 'oIFIO5GH1OjRRlBCFBQAldiLlgIs'
            headers = {
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.16(0x18001042) NetType/WIFI Language/zh_CN",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "acccept-Language": "zh-CN,zh",
                "access-token": access_token,
                "channel-id": "",
                "merchant-id": "6267a80eed218542786f1494",
                "terminal-src": "WEIXIN_MINI",
                "ver": "3.1.11"
            }
            # self.session = requests.session()
            res = self.session.get(url, headers=headers, verify=False).json()
            # print(res.text)
            try:
                res.get('data').get('cellphone')
                self.headers = headers
                self.session.headers.update(self.headers)
                return 1
            except:
                self.session.headers.update(self.headers)
                return 0
        except:
            return 0

    def check_local_login(self, phone):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/profile?merchantId=6267a80eed218542786f1494&ver=3.1.9&channelId=&src=weixin_mini&appId=wxad60dd8123a62329'
        cookies_file = '{}{}.txt'.format("%s/access_token/" % os.path.abspath(os.path.dirname(__file__)), phone)
        openid = 'oIFIO5GH1OjRRlBCFBQAldiLlgIs'
        with open(cookies_file, 'r') as f:
            access_token = f.read()
        headers = {
              "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.16(0x18001042) NetType/WIFI Language/zh_CN",
              "Accept-Encoding": "gzip, deflate, br",
              "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
              "merchant-id": "6267a80eed218542786f1494",
              "ver": "3.7.2",
              "Content-Type": "application/json",
              "access-token": access_token,
        }
        res = self.session.get(url, headers=headers, verify=False).json()
        # print(res.text)
        try:
            # print_with_time(res.get('data').get('cellphone'))
            res.get('data').get('cellphone')
            # print('%s 本地cookie登录成功' % phone)
            self.headers = headers
            self.session.headers.update(self.headers)
            return 1
        except:
            # print('%s 登录失败' % phone)
            # self.headers = headers
            # self.session.headers.update(self.headers)
            if self.buy:
                self.sms_login(phone=phone, openid=openid)
            return 0

    def get_order_list(self):
        order_list_url = 'https://m.piaoxingqiu.com/cyy_buyerapi/buyer/cyy/order/v1/order_list?orderStatusQuery=ONGOING&offset=0&length=10'
        data = {
            "merchantId": "6267a80eed218542786f1494",
            "version": "2.0.0",
            "channelId": "628204fd34113604c4351233",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329"
        }
        res = self.session.post(order_list_url, json=data, verify=False)
        # print(res.json())

    def search_show(self, keyword):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/show_list/search'
        data = {'keyword': keyword,
                'pageType': 'SEARCH_PAGE',
                'offset': 0,
                'length': 10,
                'cityId': 3101,
                'lat': '',
                'lng': '',
                'sortType': 'RECOMMEND',
                'merchantId': '6267a80eed218542786f1494',
                'version': '2.0.0',
                'channelId': '',
                'src': 'wexin_mini',
                'appId': 'wxad60dd8123a62329'}
        res = self.session.get(url, params=data, verify=False).json()
        # print(res.text)
        for i in res.get('data').get('searchData'):
            if keyword in i.get('showName'):
                print_with_time(i.get('showName'))
                showId = i.get('showId')
                stdShowId = i.get('stdShowId')
                if showId and stdShowId:
                    return showId, stdShowId
        else:
            return None, None

    def get_show_events(self, showId):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/show/%s/sessions' % showId
        data = {'merchantId': '6267a80eed218542786f1494',
                'version': '2.0.0',
                'channelId': '',
                'src': 'wexin_mini',
                'appId': 'wxad60dd8123a62329'}
        res = self.session.get(url, params=data, verify=False).json()
        sessionVOs = res.get('data').get('sessionVOs')
        return sessionVOs

    def seat_plan(self, showId, bizShowSessionId, originalPrice):
        url = 'https://m.piaoxingqiu.com/cyy_buyerapi/pub/v1/show/%s/show_session/%s/seat_plans' % (
            showId, bizShowSessionId)
        data = {'merchantId': '6267a80eed218542786f1494',
                'version': '2.0.0',
                'channelId': '',
                'src': 'wexin_mini',
                'appId': 'wxad60dd8123a62329'}
        res = self.session.get(url, params=data, verify=False).json()
        # print('waad', res)
        seatPlans = res.get('data').get('seatPlans')
        for i in seatPlans[::-1]:
            if int(i['originalPrice']) == originalPrice:
                return i['seatPlanId'], i['stdSeatPlanId']






    def pre_order(self, seatPlanId, sessionId, showId, originalPrice, amount):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/order/v3/pre_order'
        data = {
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.1.12",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329",
            "priorityId": "",
            "items": [{
                "skus": [{
                    "seatPlanId": seatPlanId,
                    "sessionId": sessionId,
                    "showId": showId,
                    "skuId": seatPlanId,
                    "skuType": "SINGLE",
                    "ticketPrice": originalPrice,
                    "qty": amount
                }],
                "spu": {
                    "id": showId,
                    "spuType": "SINGLE"
                }
            }]
        }
        res = self.session.post(url, json=data)
        print(res.json())

    def price_item(self, seatPlanId, sessionId, showId, amount, addressId, originalPrice, locationId):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/order/v3/price_items'
        data = {
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.1.12",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329",
            "productItems": [],
            "items": [{
                "skus": [{
                    "seatPlanId": seatPlanId,
                    "sessionId": sessionId,
                    "showId": showId,
                    "skuId": seatPlanId,
                    "skuType": "SINGLE",
                    "ticketPrice": originalPrice,
                    "qty": amount,
                    "deliverMethod": "EXPRESS"
                }],
                "spu": {
                    "id": showId,
                    "spuType": "SINGLE"
                }
            }],
            "locationCityId": locationId,
            "addressId": addressId
        }
        r = self.session.post(url=url, json=data, verify=False).json()
        for i in r.get('data'):
            if i.get('priceItemType') == 'EXPRESS_FEE':
                return int(i.get('priceItemVal'))
        else:
            return 0

    def get_alipay_info(self, orderId, TransactionIds):
        data = {
            "paymentProduct": "ALIPAY_WAP",
            "platform": "H5",
            "isNewCyy": True,
            "returnUrl": "https://m.piaoxingqiu.com/ticket-paid/%s" % orderId,
            "thirdPartyUserId": "",
            "transactionIds": [TransactionIds],
            "src": "WEB"
        }
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/trade/buyer/v3/payments/pay?channelId=&terminalSrc=WEB'
        r = self.session.post(url=url, json=data, verify=False).json()
        payment_url = r.get('data').get('paymentInfo')
        return payment_url



    def store_check(self, showId, bizShowSessionId):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/show/pub/v3/show/%s/show_session/%s/seat_plans_dynamic_data?merchantId=6267a80eed218542786f1494&ver=3.1.12&channelId=&src=weixin_mini&appId=wxad60dd8123a62329&showId=%s&sessionId=%s&bizSessionId=%s' % (
            showId, bizShowSessionId, showId, bizShowSessionId, bizShowSessionId)
        r = self.session.get(url, verify=False).json()
        for i in r.get('data').get('seatPlans'):
            print_with_time('%s 库存有 %s 张' % (i.get('seatPlanId'), i.get('canBuyCount')))

    def delete_audiences(self, audience_id):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user_audiences/%s?id=%s' % (audience_id, audience_id)
        data = {
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.1.13",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329"
        }
        r = self.session.delete(url=url, json=data, verify=False).json()
        if r.get('comments') == '成功':
            print('%s 删除成功' % audience_id)
        else:
            print('%s %s' % (r.get('comments')))

    def add_audiences(self, name, idNo):
        url = 'https://m.piaoxingqiu.com/cyy_gatewayapi/user/buyer/v3/user_audiences'
        data = {
            "merchantId": "6267a80eed218542786f1494",
            "ver": "3.1.13",
            "channelId": "",
            "src": "weixin_mini",
            "appId": "wxad60dd8123a62329",
            "name": "%s" % name,
            "idType": "ID_CARD",
            "idNo": "%s" % idNo,
            "bizCode": "FHL_M"
        }
        r = self.session.post(url=url, json=data, verify=False).json()
        if r.get('comments') == '成功':
            print('%s 新增成功' % name)
        else:
            print('%s %s' % (name, r.get('comments')))
