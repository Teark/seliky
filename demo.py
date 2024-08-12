import time
from seliky.seliky import WebDriver

class Page:
    """元素定位和界面信息"""
    baidu_url = "http://www.baidu.com"
    baidu_fanyi_url = "https://fanyi.baidu.com/#zh/en/"
    search_box = 'id="kw"'  # id 定位
    search_button = ['id=wrong id', '//div[@len="2"]', 'id="su"', "css=wrong css"]  # 只要有一个是对的就能定位到
    logo = '//img[@class="index-logo-src"]'  # xpath 定位
    search_words = ["小张", "小李", "小刘"]
    no_exist_button = "//no_such_button"  # 不存在的按钮


def test_baidu():
    """百度搜索测试"""
    p = Page()
    driver = WebDriver()
    driver.open_browser()
    driver.get(p.baidu_url)
    for i in p.search_words:
        driver.clear(p.search_box)  # 注意高亮
        driver.send_keys(p.search_box, i)
        driver.click(p.search_button)  # 注意高亮
        time.sleep(1)
        if driver.is_displayed(p.logo):
            print('百度logo已正确加载')
        if driver.is_visible(p.no_exist_button):
            print("是否显示方法正常")

    origin_driver = driver.driver  # selenium原生driver
    origin_driver.get(p.baidu_fanyi_url)  # 语言优势：可以使用原生driver的方法
    time.sleep(5)
    driver.quit()


if __name__ == '__main__':
    test_baidu()

"""
依次执行以下命令即可：

　　升级工具：python -m pip install --user --upgrade setuptools wheel

　　生成包：python setup.py sdist bdist_wheel

　　安装上传模块：python -m pip install --user --upgrade twine

　　上传自己的库：python -m twine upload dist/*
"""