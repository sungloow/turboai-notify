import json
import unittest
from aigc_api import AigcApi
from config import Config
from main import job_aigc


class TestAigcApi(unittest.TestCase):
    def setUp(self):
        self.aigc_api = AigcApi()
        self.aigc_api.login()

    def test_get_token(self):
        token_data = self.aigc_api.get_token()
        print(json.dumps(token_data, ensure_ascii=False, indent=4))
        self.assertIsNotNone(token_data)


class TestMain(unittest.TestCase):
    def setUp(self):
        pass

    def test_job_aigc(self):
        job_aigc()