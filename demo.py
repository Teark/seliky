import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

bs = webdriver.Chrome()
bs.get("https://fanyi.baidu.com/#zh/en/%E4%BD%93%E9%AD%84%2C%E6%8A%80%E6%9C%AF%2C%E8%8B%B1%E8%AF%AD")

xx = '//span[@class="app-guide-close"]'
i1 = '//textarea[@id="baidu_translate_input"]'
duizhao = '//span[@class="op-check"]'

# 弹窗判断
try:
    x1 = WebDriverWait(bs, 3).until(
        ec.visibility_of_element_located((By.XPATH, xx)))
    print("弹窗加载到dom: ", x1)
    x1.click()
except TimeoutException:
    print("弹窗没加载到dom:", False)

try:
    x2 = WebDriverWait(bs, 3).until(
        ec.visibility_of_element_located((By.XPATH, i1)))
    print("输入框可见: ", x2)  # 此时输入框被遮住了但还是显示可见。由此得知，可见还是不可见并不是以人眼为标准，而是以层级里的元素是否展示了为准。
    x2.click()
    x2.send_keys("你好世界")
except (TimeoutException, ElementClickInterceptedException):
    print("输入框不可见或被遮住了，或不可点击")

try:
    x2 = WebDriverWait(bs, 10).until(
        ec.visibility_of_element_located((By.XPATH, duizhao)))
    print("隐藏按钮可见: ", x2)  # 此时输入框被遮住了但还是显示可见。由此得知，可见还是不可见并不是以人眼为标准，而是以层级里的元素是否展示了为准。
    x2.click()
except (TimeoutException, ElementClickInterceptedException):
    print("隐藏按钮不可见或被遮住了，或不可点击")

try:
    x2 = WebDriverWait(bs, 10).until(
        ec.visibility_of_element_located((By.XPATH, duizhao)))
    print("隐藏按钮可见: ", x2)  # 此时输入框被遮住了但还是显示可见。由此得知，可见还是不可见并不是以人眼为标准，而是以层级里的元素是否展示了为准。
    x2.click()
except (TimeoutException, ElementClickInterceptedException):
    print("隐藏按钮不可见或被遮住了，或不可点击")

"""--------------------------------------------------------"""
b1 = bs.find_element(By.XPATH, duizhao)
print(b1.is_selected())
print(b1.is_displayed())
print(b1.is_enabled())
time.sleep(5)
bs.quit()

"""
结论：
1：presence_of_element_located: 是否加载到dom树
2：visibility_of_element_located：是否"可见"，可见还是不可见并不是以人眼为标准，加载到dom树且长宽大于0。
ui自动化中操作的元素一般都是有长宽的，所以绝大大部分情况下，用2更好。
presence_of_element_located的校验程度轻一些，在页面跳转之后判断某种标志是否出现用这个快一些；特殊情况下校验无边框的元素也会用到这个。
"""
