from apscheduler.schedulers.background import BackgroundScheduler
from urllib.parse import quote, urljoin
import time
import logging

from DingTalkBot import DingTalkBot
from aigc_api import AigcApi
from config import config


def setup_logging():
    log_level = config.get("logging", "level", "DEBUG")
    log_path = config.get("logging", "path", "app.log")

    # Convert log level to uppercase
    log_level = getattr(logging, log_level.upper(), logging.DEBUG)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create file handler
    file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def do_job_aigc(scheduler=None):
    dingtalk_conf = config.get_dingtalk()
    webhook = dingtalk_conf.get("webhook")
    secret = dingtalk_conf.get("secret")
    bot = DingTalkBot(webhook, secret)
    aigc_api = AigcApi()
    login = aigc_api.login()
    if not login:
        bot.send_text("TurboAI登录失败")
        return
    token_data = aigc_api.get_token()
    success_token = bool(token_data.get("success"))
    one_yuan_units = config.get("turboai", "units", 500000)
    text = ""
    action_card_btns = []
    if success_token:
        data = token_data.get("data")
        name = data.get("name")
        used_quota = data.get("used_quota")
        unlimited_quota = data.get("unlimited_quota")
        remain_quota = data.get("remain_quota")
        credit = remain_quota / one_yuan_units
        credit = round(credit, 2)
        used_credit = used_quota / one_yuan_units
        used_credit = round(used_credit, 2)
        key = data.get("key")
        masked_key = key[:3] + "*" * 5 + key[-5:]
        text += f"**令牌名称:** {name}  \n  **令牌密钥:** {masked_key}"
        currency = config.get("turboai", "currency", "¥")
        if unlimited_quota:
            text += f"  \n  **剩余额度:** 无限制  \n  **已用额度:** {currency}{used_credit}"
        else:
            text += f"  \n  **剩余额度:** **{currency}{credit}**  \n  **已用额度:** {currency}{used_credit}"

        if 16 <= time.localtime().tm_hour <= 19:
            try:
                today_request_count, today_cost, total_tokens_today = aigc_api.get_dashboard_with_log()
                text += f"  \n"
                text += f"  \n  今日消费: {currency}{today_cost}"
                text += f"  \n  今日请求: {today_request_count}次"
                text += f"  \n  今日Token: {total_tokens_today}"
            except Exception as e:
                logging.error(f'获取今日消费信息失败, msg: {e}')

        if credit < 1:
            text += f"  \n  *余额不足，请及时充值*"
            aigc_api_host = config.get("turboai", "host", "https://api.turboai.one")
            action_url = urljoin(aigc_api_host, "/panel/topup")
            external_page_url = f"dingtalk://dingtalkclient/page/link?url={quote(action_url, 'utf-8')}&pc_slide=false"
            action_card_btns.append(
                {"title": "立即充值", "actionURL": external_page_url}
            )

        if scheduler:
            current_job = scheduler.get_jobs()[0]
            if credit < 0.5:
                current_job.reschedule(
                    trigger="cron", day_of_week="mon-fri", hour="9-18", minute=0
                )
                logging.info("TurboAI Credit is less than 0.5. Switching to every hour.")
            else:
                current_job.reschedule(
                    trigger="cron", day_of_week="mon-fri", hour="9,17", minute=0
                )
                logging.info("TurboAI Credit is sufficient. Switching to 9:00 and 17:00.")
    else:
        msg = token_data.get("message")
        text += f"TurboAI余额查询失败, msg: {msg}"

    logging.info(text)
    title = "TurboAI 余额"
    bot.send_action_card(title=title, text=text, btns=action_card_btns)


def job_aigc(scheduler=None):
    try:
        do_job_aigc(scheduler)
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    setup_logging()
    background_scheduler = BackgroundScheduler()
    job_aigc = background_scheduler.add_job(
        job_aigc,
        "cron",
        day_of_week="mon-fri",
        hour="9-17",
        minute="*/30",
        args=[background_scheduler],
    )
    logging.info("TurboAI notify app is running.")
    background_scheduler.start()

    try:
        # This is here to simulate application activity (which keeps the main thread alive).
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        background_scheduler.shutdown()
