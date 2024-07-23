import toml

class Config:
    def __init__(self, filename="config.toml"):
        self.config = toml.load(filename)

    def get(self, section, key=None, default=None):
        section_data = self.config.get(section, {})
        if key:
            return section_data.get(key, default)
        return section_data

    def active_dingtalk(self):
        return self.get('active_dingtalk', 'active', 'test')

    def get_dingtalk(self):
        active_dingtalk = self.active_dingtalk()
        return self.config.get(f'dingtalk-{active_dingtalk}', {})

    def get_turboai(self):
        return self.config.get('turboai', {})


config = Config()


if __name__ == "__main__":
    config = Config('config.toml')
    dingtalk_webhook = config.get('dingtalk', 'webhook', 'default_webhook')
    print(f"DingTalk Test Webhook: {dingtalk_webhook}")