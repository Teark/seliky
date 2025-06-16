from seliky.seliky_dri import WebDriver


def ui():
    """
    看走势截图
    """
    bs = WebDriver()
    bs.open_browser()
    bs.get('https://sahitest.com/demo')
    bs.click('Link Test', bac_sleep=3)
    bs.get('https://sahitest.com/demo')
    bs.click('Form Test', bac_sleep=3)
    bs.get('https://sahitest.com/demo')
    bs.click('Label Page', bac_sleep=3)


if __name__ == '__main__':
    ui()