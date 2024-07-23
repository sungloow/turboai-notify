import base64
import hashlib
import hmac
import logging
import time
import urllib

import requests


class DingTalkBot(object):
    def __init__(self, _webhook, _secret=None):
        self.webhook = _webhook
        self.secret = _secret

    def __get_signature(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def __do_send_request(self, _data, _headers=None):
        if self.secret:
            self.webhook += "&timestamp={}&sign={}".format(*self.__get_signature())
        res = requests.post(self.webhook, headers=_headers, json=_data)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("errmsg") == "ok":
                return True
            else:
                raise Exception(res_json)
        else:
            raise Exception(
                "发送钉钉通知失败，网络错误，错误码为: " + str(res.status_code)
            )

    def __send_request(self, _data, _headers=None):
        for i in range(5):
            try:
                self.__do_send_request(_data, _headers)
                logging.info("发送钉钉通知成功")
                break
            except Exception as e:
                logging.error(f'发送钉钉通知失败，错误提示：{e.args[0].get("errmsg")}')
                logging.warning("Wait 2 seconds and retry...")
                time.sleep(2)
                if e.args[0].get("errcode") == 460101:
                    logging.warning("通知内容过长，已截断。")
                    if _data.get("text") and _data.get("text").get("content"):
                        _data.get("text").update(
                            {
                                "content": f'{_data.get("text").get("content")[:10000]}...'
                            }
                        )
                    if _data.get("markdown") and _data.get("markdown").get("text"):
                        _msg_body = "内容过长，不显示"
                        _data.get("markdown").update(
                            {
                                "text": f'{_data.get("markdown").get("title")} \n\n {_msg_body}'
                            }
                        )
                    continue

    def send_text(self, _text):
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "msgtype": "text",
            "text": {
                "content": _text,
            },
        }
        self.__send_request(data, headers)

    def send_markdown(self, title, text, at_mobiles=None, at_user_ids=None):
        if at_user_ids is None:
            at_user_ids = []
        if at_mobiles is None:
            at_mobiles = []
        data = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": text},
            "at": {
                "atMobiles": at_mobiles,
                "atDingtalkIds": at_user_ids,
                "isAtAll": False,
            },
        }
        self.__send_request(data)

    def send_action_card(self, title, text, btns=[], btn_orientation=0):
        """独立跳转 ActionCard 类型

        Args:
            title (_type_): title
            text (_type_): text
            btns (list, optional): example: [{"title": "内容不错", "actionURL": "https://www.dingtalk.com/"}, {"title": "不感兴趣", "actionURL": "https://www.dingtalk.com/"}],
            btn_orientation (int, optional): 按钮排列方式: 0(按钮竖直排列), 1(按钮横向排列)
        """
        data = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "btnOrientation": btn_orientation,
                "btns": btns,
            },
        }
        self.__send_request(data)
