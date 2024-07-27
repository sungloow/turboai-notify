import logging
import time

import requests
from urllib.parse import urljoin
from datetime import datetime

from config import config

def get_start_of_day_timestamp():
    # 获取当前日期
    today = datetime.now().date()
    # 创建今天的开始时间 00:00:00
    start_of_day = datetime(today.year, today.month, today.day)
    # 转换为 Unix 时间戳
    start_timestamp = int(start_of_day.timestamp())
    return start_timestamp


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
        self.logged = False

    def login(self, max_attempts=5):
        for attempt in range(max_attempts):
            json_data = {
                "username": self.turboai.get("username"),
                "password": self.turboai.get("password"),
            }
            url = urljoin(self.host_url, "/api/user/login")
            response = self.session.post(url=url, headers=self.headers, json=json_data)
            rj = response.json()
            if rj.get("success"):
                self.logged = True
                logging.info("Login successful.")
                return True
            else:
                # 延迟，避免过于频繁的尝试
                if attempt < max_attempts - 1:
                    logging.warning(f"Login failed. Retrying ({attempt + 1}/{max_attempts})...")
                    time.sleep(2)  # 等待2秒后再尝试
        logging.error("Login failed. Maximum attempts reached.")
        return False

    @staticmethod
    def require_login(func):
        def wrapper(self, *args, **kwargs):
            if not self.logged:
                if not self.login():
                    raise Exception("Login failed. Please check your credentials.")
            return func(self, *args, **kwargs)
        return wrapper

    @require_login
    def get_self(self):
        url = urljoin(self.host_url, "/api/user/self")
        response = self.session.get(url=url, headers=self.headers)
        return response.json()

    @require_login
    def get_token(self, key_id: str = None):
        if key_id is None:
            key_id = self.turboai.get("key_id")
        url = urljoin(self.host_url, f"/api/token/{key_id}")
        res = self.session.get(url=url, headers=self.headers)
        rj = res.json()
        return rj

    @require_login
    def get_dashboard(self):
        """
        获取仪表板数据，包括今天的请求计数、成本和token使用情况。

        :return: Tuple of (today's request count, today's cost, today's token usage)
        """
        url = urljoin(self.host_url, "/api/user/dashboard")
        res = self.session.get(url=url, headers=self.headers)
        rj = res.json()
        success = rj.get("success")
        if not bool(success):
            logging.error(f"Unexpected error: {rj}")
            raise Exception(f"Unexpected error: {rj}")
        data = rj.get("data")
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        # Initialize variables to store today's data
        today_request_count = 0
        today_prompt_tokens = 0
        today_completion_tokens = 0
        # Iterate through the data to find today's statistics
        for entry in data:
            if entry["Date"] == today_date_str:
                today_request_count += entry["RequestCount"]
                today_prompt_tokens += entry["PromptTokens"]
                today_completion_tokens += entry["CompletionTokens"]
        # Calculate total tokens used today
        total_tokens_today = today_prompt_tokens + today_completion_tokens
        # 数据中没有直接提供成本，无以获取今天的成本
        today_cost = 0
        return today_request_count, today_cost, total_tokens_today

    @require_login
    def get_dashboard_with_log(self, start_timestamp: int = None, end_timestamp: int = None):
        """
        通过日志获取仪表板数据，包括今天的请求计数、成本和token使用情况。

        :return: Tuple of (today's request count, today's cost, today's token usage)
        """
        self.headers['referer'] = 'https://api.turboai.io/panel/log'
        token_name = self.get_token()['data']['name']
        start_timestamp = get_start_of_day_timestamp() if start_timestamp is None else start_timestamp
        end_timestamp = int(datetime.now().timestamp()) if end_timestamp is None else end_timestamp
        # 初始化变量存储今天的统计数据
        today_request_count = 0
        today_prompt_tokens = 0
        today_completion_tokens = 0
        today_cost = 0

        page = 1
        size = 100
        total_count = 0  # 初始化总条数
        url = urljoin(self.host_url, "/api/log/self")
        while True:
            params = {
                'page': str(page),
                'size': str(size),
                'order': '-created_at',
                'p': '0',
                'token_name': str(token_name),
                'model_name': '',
                'start_timestamp': str(start_timestamp),
                'end_timestamp': str(end_timestamp),
                'log_type': '0',
            }
            res = self.session.get(url=url, params=params, headers=self.headers)
            rj = res.json()
            # 检查是否成功
            success = rj.get("success", False)
            if not success:
                logging.error(f"Unexpected error: {rj}")
                raise Exception(f"Unexpected error: {rj}")
            data = rj.get("data", {}).get("data", [])
            if not data:
                break
            # 更新统计数据
            for entry in data:
                today_request_count += 1
                today_prompt_tokens += entry["prompt_tokens"]
                today_completion_tokens += entry["completion_tokens"]
                today_cost += entry["quota"]
            # 检查是否已经是最后一页
            current_page_info = rj.get("data", {})
            current_total_count = current_page_info.get("total_count", 0)
            if total_count == 0:
                total_count = current_total_count  # 第一次获取总条数
            if (page - 1) * size + len(data) >= total_count:
                break
            page += 1

        total_tokens_today = today_prompt_tokens + today_completion_tokens
        total_tokens_today = f'{total_tokens_today / 1000:.2f}k' if total_tokens_today > 1000 else f'{total_tokens_today}'
        units = config.get("turboai", "units", 500000)
        today_cost = round(today_cost / units, 3)
        return today_request_count, today_cost, total_tokens_today

