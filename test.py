import json
import time
import unittest

from aigc_api import AigcApi
from main import job_aigc


class TestAigcApi(unittest.TestCase):
    def setUp(self):
        self.aigc_api = AigcApi()
        # self.aigc_api.login()

    def test_get_token(self):
        token_data = self.aigc_api.get_token()
        print(json.dumps(token_data, ensure_ascii=False, indent=4))
        self.assertIsNotNone(token_data)

    def test_get_dashboard(self):
        dashboard_data = self.aigc_api.get_dashboard()
        print(json.dumps(dashboard_data, ensure_ascii=False, indent=4))
        self.assertIsNotNone(dashboard_data)

    def test_get_dashboard_with_log(self):
        dashboard_data = self.aigc_api.get_dashboard_with_log(
            start_timestamp=1721491200, end_timestamp=1721577600
        )
        print(json.dumps(dashboard_data, ensure_ascii=False, indent=4))
        self.assertIsNotNone(dashboard_data)


class TestMain(unittest.TestCase):
    def setUp(self):
        pass

    def test_job_aigc(self):
        job_aigc()
