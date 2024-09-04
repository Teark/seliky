from seliky.seliky import WebDriver, Keys

driver = WebDriver(executable_path=r'c:\chromedriver.exe')
driver.open_browser()
driver.get("https://www.baidu.com")
search_words = ["小张", "小李", "小刘"]
for i in search_words:
    driver.send_keys('//input[@id="kw"]', i)
    driver.press(Keys.CONTROL, 'a')
    driver.click('//input[@id="su"]')
    if driver.is_visible('//img[@class="index-logo-src"]'):
        print('百度logo已正确加载')

"""
依次执行以下命令即可：
　　升级工具：python -m pip install --user --upgrade setuptools wheel
　　安装上传模块：python -m pip install --user --upgrade twine
　　生成包：python setup.py sdist bdist_wheel
　　上传自己的库：python -m twine upload dist/*
"""
