"""
this is a demo file let you know how to use and how convenient it is!
how to use in python, how to use in robotframework, se bellow
"""

import time
from WebDriver2 import WebDriver2  # 自带高亮


class Page:
    """元素定位和界面信息"""
    baidu_url = "http://www.baidu.com"
    baidu_fanyi_url = "https://fanyi.baidu.com/#zh/en/"
    search_box = 'id=kw'
    search_button = ['id=wrong id', '//@class=wrong xpath', 'id=su', "css=wrong css"]  # 只要有一个是对的就能定位到
    search_words = ["小唐", "小李", "小刘"]


def test_baidu():
    """百度搜索测试"""
    p = Page()
    driver = WebDriver2()
    driver.get(p.baidu_url)
    for i in p.search_words:
        driver.clear(p.search_box)
        driver.send_keys(i, p.search_box)
        driver.click(p.search_button)
        time.sleep(1)
    time.sleep(3)
    origin_driver = driver.driver  # selenium原生driver
    origin_driver.get(p.baidu_fanyi_url)  # 语言优势：可以使用原生driver的方法
    time.sleep(5)
    driver.quit()


if __name__ == '__main__':
    test_baidu()

"""
How to use in robotframework?
========================================================================================================================
*** Settings ***
Library            WebDriver2.py

*** Variables ***
# 元素定位和界面信息
${baidu_url}  http://www.baidu.com
${baidu_fanyi_url}  "https://fanyi.baidu.com/#zh/en/"
${search_box}  id=kw
@{search_button}    id=wrong id     //@class=wrong xpath    id=su   css=wrong css    # 弹性定位：列表中只要有一个元素是对的，就能定位到
@{search_words}     小唐       小李      小刘


*** Test Cases ***
# 百度搜索测试
demo
    get     ${baidu_url}      # 进入百度首页
    FOR     ${i}    IN     @{search_words}
        clear   ${search_box}  # 清除搜索框
        send keys    ${i}   ${search_box}  # 搜索框输入搜索词
        click    ${search_button}  # 点击搜索按钮
    END
    sleep    3
    quit
"""
