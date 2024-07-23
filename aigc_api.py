import requests
from urllib.parse import urljoin

from config import config


class AigcApi:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "priority": "u=1, i",
        "referer": "https://api.turboai.one",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    def __init__(self):
        self.session = requests.session()
        self.turboai = config.get_turboai()
        self.host_url = self.turboai.get("host")

    def login(self):
        json_data = {
            "username": self.turboai.get("username"),
            "password": self.turboai.get("password"),
        }
        url = urljoin(self.host_url, "/api/user/login")
        response = self.session.post(url=url, headers=self.headers, json=json_data)
        rj = response.json()
        return bool(rj.get("success"))

    def get_self(self):
        url = urljoin(self.host_url, "/api/user/self")
        response = self.session.get(url=url, headers=self.headers)
        return response.json()

    def get_token(self, key_id=None):
        if key_id is None:
            key_id = self.turboai.get("key_id")
        url = urljoin(self.host_url, f"/api/token/{key_id}")
        res = self.session.get(url=url, headers=self.headers)
        rj = res.json()
        return rj

    def get_dashboard(self):
        """
        dashboard
        :return: 今日请求, 今日消费, 今日Token
        """
        url = urljoin(self.host_url, "/api/user/dashboard")
        res = self.session.get(url=url, headers=self.headers)
        rj = res.json()
        success = rj.get("success")
        if not bool(success):
            return None, None, None
        data = rj.get("data")
        return None, None, None

