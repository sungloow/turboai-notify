"""
节假日相关的工具方法
"""

from datetime import datetime
import json
import logging
import os
import requests
from typing import Optional


def fetch_holiday(year: Optional[int] = None) -> Optional[list[dict]]:
    """
    从API获取指定年份的节假日信息

    Args:
        year: 年份，默认为当前年份

    Returns:
        节假日信息列表，如果获取失败则返回None
        数据示例：
        [
            {

                "date": "2024-01-01",
                "days": 1,
                "holiday": true,
                "name": "元旦节"
            },
            ...
        ]
    """

    year = datetime.now().year if year is None else year

    url = f"https://date.appworlds.cn/year/{year}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        rj = response.json()
        if rj.get("code") != 200:
            logging.error(f"获取节假日信息失败, msg: {rj.get('msg')}")
            return None
        return rj.get("data", [])
    except requests.RequestException as e:
        logging.error(f"请求节假日信息失败: {e}")
        return None


def save_holiday(holiday_info: list[dict], year: int) -> None:
    """
    保存节假日信息到本地文件

    Args:
        holiday_info: 节假日信息列表
        year: 年份
    """
    filename = f"{year}.json"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(holiday_info, f, ensure_ascii=False, indent=4)
        logging.info(f"节假日信息已保存到 {filename}")
    except IOError as e:
        logging.error(f"保存节假日信息失败: {e}")


def load_or_fetch_holiday_info(year: int) -> list[dict]:
    """
    加载或获取指定年份的节假日信息

    Args:
        year: 年份

    Returns:
        节假日信息列表，如果获取失败则返回None
    """
    filename = f"{year}.json"

    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                holiday_info = json.load(f)
            if holiday_info:
                return holiday_info
        except (IOError, json.JSONDecodeError) as e:
            logging.warning(f"读取本地节假日信息失败: {e}")

    holiday_info = fetch_holiday(year)
    if holiday_info is None or not holiday_info:
        logging.warning(f"无法获取{year}年的节假日信息，将使用默认周末判断")
        return []
    save_holiday(holiday_info, year)
    return holiday_info


def is_workday(date: Optional[str] = None) -> bool:
    """
    判断指定日期是否为工作日

    Args:
        date: 日期，默认为当前日期

    Returns:
        True: 是工作日
        False: 不是工作日
    """
    date = datetime.now() if date is None else datetime.strptime(date, "%Y-%m-%d")

    year = date.year
    holiday_info = load_or_fetch_holiday_info(year)

    date_str = date.strftime("%Y-%m-%d")
    for info in holiday_info:
        if info.get("date") == date_str:
            return not info.get("holiday", False)

    # 如果没有特殊节假日信息，则按照常规工作日判断
    return date.weekday() < 5


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"今天（{today}）是否工作日：", is_workday())
    print(f"2024-09-29 是否工作日：{is_workday('2024-09-29')}")
    print(f"2024-10-04 是否工作日：{is_workday('2024-10-04')}")
    print(f"2024-10-05 是否工作日：{is_workday('2024-10-05')}")
    print(f"2024-10-12 是否工作日：{is_workday('2024-10-12')}")
