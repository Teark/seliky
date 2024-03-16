import shutil
from datetime import datetime, timedelta
import platform

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, \
    StaleElementReferenceException, TimeoutException, ElementNotInteractableException, InvalidSelectorException, \
    MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webdriver import WebDriver as Wd
import inspect
import re
import time
import sys
from functools import wraps
import os
import ctypes
import threading
from hashlib import md5


class WebDriver:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    SLEEP = 0.01  # 前后置等待初始时间
    INTERVAL = 0.01  # 最佳值范围：（0.01~0.05）

    def __init__(
            self,
            executable_path: str = '',
            display: bool = True,
            logger=None,  # pytest-loguru object
            options: list = '',
            experimental_option: dict = '',
            log_locator: bool = False,
    ):
        """
        :param executable_path: 驱动路径
        :param display: 是否以界面方式显示
        :param options: 设置项，例如:
            '--headless'
            '--no-sandbox'
            '--disable-gpu'
            '--disable-dev-shm-usage'
            'window-size=1920x1080'
            'blink-settings=imagesEnabled=False'
            'user-agent="MQQBrowser/26 Mozilla/5.0 ..."'
            'user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'
        :param experimental_option: 特殊设置项，例如: 不加载图、取消弹窗询问、设置下载路径
            prefs =
            {'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.popups': 0,
             'download.default_directory': r'd:\'}
        适配关系：火狐86-0.30；谷歌114-11988k
        注：火狐浏览器父路径必须为Mozilla Firefox
        """
        self.display = display
        self.options = options
        self.experimental_option = experimental_option
        self.executable_path = executable_path
        self.logger = logger
        self.driver: Wd
        self.log_locator = log_locator

    def open_browser(self):
        """打开浏览器，默认打开谷歌"""
        executable_path = self.executable_path.lower()

        if 'chrome' in executable_path or not executable_path:  # 默认没用时用谷歌浏览器
            browser_type = 'chrome'
            opt = ChromeOptions()
            for i in self.options:
                opt.add_argument(i)

            if self.experimental_option:
                for k, v in self.experimental_option.items():
                    opt.add_experimental_option(k, v)
            opt.add_experimental_option('excludeSwitches', ['enable-logging'])  # 避免usb打印错误

        else:
            browser_type = 'firefox'
            global BROWSER
            BROWSER = browser_type
            opt = FirefoxOptions()
            if self.experimental_option:
                for k, v in self.experimental_option.items():
                    opt.set_preference(k, v)
        opt.set_capability('pageLoadStrategy', 'normal')
        exist_driver = True
        if not executable_path or not os.path.exists(executable_path):
            exist_driver = False  # 有的放在python目录下就无需配置

        try:
            if platform.system().lower() in ["windows", "macos"] and self.display:
                if browser_type == 'chrome':
                    from selenium.webdriver.chrome.service import Service
                    self.driver = webdriver.Chrome(options=opt, service=Service(
                        executable_path=executable_path) if exist_driver else None)
                else:
                    from selenium.webdriver.firefox.service import Service
                    opt.binary = FirefoxBinary()  # 当前版本的得保留这一句
                    # self.driver = webdriver.Firefox(options=opt, service=Service(
                    #     executable_path=executable_path) if exist_driver else None)  # 这样启动会报错
                    # self.driver = webdriver.Firefox()
                    self.driver = webdriver.Firefox(options=opt, service=Service(
                        executable_path=executable_path, log_path=os.devnull, log_output=os.devnull))  # 有意思，继续调试
                self.driver.maximize_window()

            else:  # 无界面方式/流水线
                for i in ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']:
                    opt.add_argument(i)
                if browser_type == 'chrome':
                    self.driver = webdriver.Chrome(options=opt)
                else:
                    self.driver = webdriver.Firefox(options=opt)
                self.driver.maximize_window()
            global g_driver
            g_driver = self.driver
            time.sleep(1)  # 有user-dir的时候最好等待一下
        except WebDriverException as e:
            raise e
        return self.driver

    def __highlight__(self, ele, count=2):
        """每一步的高亮"""
        if count is None:
            count = 2
        if count < 0:  # 为0时闪的很快，不会间隔闪烁，为-1表示不希望高亮
            return
        js = 'arguments[0].style.border='
        js2 = 'arguments[0].style.outline='  # 不占据空间但有的不亮
        """
        好看的色码：红色-#FF0000；海蓝-#70DB93;黄色-#FFFF00；淡紫色-#DB7093；青色-#00FFFF；天蓝-#38B0DE
        """
        if self.display:
            try:
                for _ in range(count):
                    self.driver.execute_script(js + '"2px solid #FF0000"', ele)
                    self.driver.execute_script(js2 + '"2px solid #FF0000"', ele)
                    time.sleep(self.INTERVAL)
                    self.driver.execute_script(js + '"2px solid #FFFF00"', ele)
                    self.driver.execute_script(js2 + '"2px solid #FFFF00"', ele)
                    time.sleep(self.INTERVAL)
                self.driver.execute_script(js + '"2px solid #FF0000"', ele)
                self.driver.execute_script(js2 + '"2px solid #FF0000"', ele)
                time.sleep(self.INTERVAL)
                if count:
                    time.sleep(self.INTERVAL * 4)
                self.driver.execute_script(js + '""', ele)
                self.driver.execute_script(js2 + '""', ele)
            except WebDriverException:
                ...

    def __fe__(self, by, locator_, timeout):
        @overtime(timeout)
        def fe():
            self.driver.find_elements(by=by, value=locator_)
            time.sleep(0.05)
            return self.driver.find_elements(by=by, value=locator_)

        eles = fe()[:100]
        for i in eles:
            try:
                i
            except StaleElementReferenceException:
                raise StaleElementReferenceException
        return eles

    def _filter_(self, _elems_, times=0):
        """3次过滤，除去没有坐标的，里面的元素在那个变化的瞬间是可能会变化的，所以需要多次过滤，至少2次过滤"""
        elems = []
        if times >= 3:
            return _elems_  # _elems_为洗过之后的
        for i in _elems_:
            try:
                if i.location['x'] and i.location['y']:
                    elems.append(i)
            except (StaleElementReferenceException, WebDriverException):
                continue
        return self._filter_(elems, times=times + 1)

    def __find_ele(self, locator_, index: int = 0, timeout: float = 8.0, **kwargs):
        y = timeout % 1
        interval = [1.0 for _ in range(int(timeout))]
        if y:
            interval.append(y)
        use_location = kwargs.get('use_location', True)
        raise_ = kwargs.get('raise_', True)
        try:
            for _ in interval:
                try:
                    elems = self.__fe__('xpath', locator_, _)
                except TimeoutError:
                    continue  # TimeoutError里面已经耗时过了，这里无需再sleep
                except (InvalidSelectorException, StaleElementReferenceException):
                    time.sleep(_ * 0.3)  # 这两个不知道会耗时多少，剩余的时间取其三分
                    continue
                if not elems:
                    time.sleep(min([timeout, 0.9]))
                    continue
                # 数据清洗
                if index == 999:  # 999为元素列表
                    elem = elems
                elif not index and len(elems) > 1 and use_location:  # 无索引且有多个元素时，-1时不用清洗
                    elem = self._filter_(elems)
                    if not elem:
                        time.sleep(0.9)
                        continue
                    elem = elem[0]
                else:  # 有索引的
                    elem = elems[index]
                    count = kwargs.get('count')
                    self.__highlight__(elem, count=count)
                return elem
        except Exception as e:
            if raise_:
                raise e

    def _locator_(self, locator, vague=False):
        """返回 真实locator，描述，是否为Web对象"""
        if isinstance(locator, tuple):
            if len(locator) == 1:
                real_locator, desc = locator[0], ''
            else:
                real_locator, desc = locator[:2]
        elif isinstance(locator, str) or isinstance(locator, int):
            locator = str(locator)
            desc = self.__get_locator_future__(locator)
            if locator.startswith("/") or locator.startswith("(/"):
                real_locator = locator
            else:
                real_locator = "//div[text()='{0}'] | //span[text()='{0}'] | //a[text()='{0}'] | //p[text()='{0}'] |" \
                               " //label[text()='{0}'] | //td[text()='{0}'] | li[text()='{0}']".format(locator)
                if vague:
                    real_locator = "//div[contains(text(),'{0}')] | //span[contains(text(),'{0}')] |" \
                                   " //a[contains(text(),'{0}')] | //label[contains(text(),'{0}')] |" \
                                   " //td[contains(text(),'{0}')] | //li[contains(text(),'{0}')] |" \
                                   " //p[text()='{0}'] |".format(locator)
        else:
            raise TypeError
        return real_locator, desc

    def _ele_(self, locator, index=0, timeout=8.0, **kwargs):
        """
        查找元素
        """
        if isinstance(locator, WebElement):
            return locator
        vague = kwargs.get('vague', False)
        logged = kwargs.get('logged', True)
        raise_ = kwargs.get('raise_', True)
        locator, desc = self._locator_(locator, vague=vague)

        # 获取描述（有反射机制莫再封，反射机制只针对当前文件对它的引用）
        desc = self.__operate__().get(inspect.stack()[1].function, '') + desc
        if self.log_locator:
            desc = desc + ' ' + locator
        ele = self.__find_ele(locator_=locator, index=index, timeout=timeout, **kwargs)
        if ele:
            if logged:  # send_keys 无需记录因其外层有记录
                msg = "✔ %s" % (desc if desc else locator)
                self.logger.info(msg) if self.logger else print(msg)
            return ele
        else:
            if not raise_:  # 指定不抛出异常时也无需记录
                logged = False
            if logged:
                msg = "❌ %s" % desc if desc else locator
                self.logger.error(msg) if self.logger else print(msg)
            if raise_:
                raise ValueError("没找到元素 %s, 请检查表达式" % locator)

    def click(self, locator, index: int = 0, timeout=8, pre_sleep=SLEEP, bac_sleep=SLEEP, raise_: bool = True,
              vague=False):
        """
        点击元素
        关于sleep：前后加起来0.1秒，提升页面加载容错性，视觉停留只是其次，0.05是最低最合适的值
        """
        time.sleep(pre_sleep)
        elem = self._ele_(locator, index, timeout, raise_=raise_, vague=vague)
        try:
            elem.click()
            time.sleep(bac_sleep)
        except Exception as e:
            msg = "原生点击失败，尝试js点击"
            self.logger.warning(msg) if self.logger else print(msg)
            try:
                # 可以穿透遮罩层，可解决ElementClickInterceptedException
                self.driver.execute_script("arguments[0].click();", elem)
            except Exception as e2:
                msg = "js点击失败，尝试鼠标点击"
                self.logger.warning(msg) if self.logger else print(msg)
                try:
                    # 不可穿透遮罩层（手动鼠标形式点击），可解决ElementClickInterceptedException; StaleElement
                    self.ac_click(locator, index=index)
                except Exception as e3:
                    if raise_:
                        raise e3
                    else:
                        msg = '鼠标点击失败 %s' % (
                                str(locator) + str(e3)[:10] + '...' + str(e)[:10] + '...' + str(e2)[:10]
                        )
                        self.logger.error(msg) if self.logger else print(msg)
        return elem

    def ac_click(self, locator, index=0):
        """鼠标点击"""
        return self.move_to_element(locator=locator, index=index, click=True)

    def send_keys(self, locator, value, index: int = 0, timeout: int = 6, clear: bool = True,
                  pre_sleep=SLEEP, bac_sleep=SLEEP, raise_=True, enter=False):
        """
        输入框输入值，上传请用upload方法
        """
        if value is None or value is '':  # 0可以有
            return
        time.sleep(pre_sleep)
        locator_, desc = self._locator_(locator)
        msg = '✔ 输入 ' + desc + ' ' + str(value)

        def normal_send():
            elem = self._ele_(locator, index, timeout, raise_=raise_)
            if not elem:
                return False
            if clear:
                try:
                    elem.clear()  # 日期输入框清空可能会 invalid element state
                    time.sleep(0.1)
                    elem.clear()  # 清空2次 兼容有些框框
                except Exception as e1:
                    try:
                        elem.send_keys(Keys.CONTROL, "a")
                    except Exception as e2:
                        msgf = "❕ clear失败-无妨" + str(e1)[-1] + "全选删除失败-无妨" + str(e2)
                        self.logger.error(msgf) if self.logger else print(msgf)  # 清空失败不抛出仅记录
            try:
                elem.send_keys(value)
                self.logger.info(msg) if self.logger else print(msg)
                if enter:
                    time.sleep(0.1)  # 有一些需要预加载否则直接enter没反应过来
                    elem.send_keys(Keys.ENTER)
            except Exception as e:
                msg1 = '❕ 输入值方式1失败' + str(e)[9:38] + '...'
                self.logger.warning(msg1) if self.logger else print(msg1)
                return False
            time.sleep(bac_sleep)
            return True

        def active_send():
            try:
                if locator:  # locator为假时填值的是页面已定位的框框
                    self.move_to_element(locator=locator_, index=index, click=True, logged=False)
                if clear:
                    self.switch_to.active_element.send_keys(Keys.CONTROL, "a")
                    self.switch_to.active_element.send_keys(Keys.DELETE)  # 某些情况能避免满屏被选中
                self.switch_to.active_element.send_keys(value)
                if enter:
                    self.switch_to.active_element.send_keys(Keys.ENTER)
                self.logger.info(msg) if self.logger else print(msg)
            except Exception as e:
                msg1 = '❕ 输入值方式2失败' + str(e)[9:38] + '...'
                self.logger.warning(msg1) if self.logger else print(msg1)
                return False
            return True

        if not normal_send():
            return active_send()

    def upload(self, locator, file_path: str, index=0, timeout=8):
        """
        上传，内部还是send_keys，处理windows弹窗上传请用uploads库
        """
        elem = self._ele_(locator, index, timeout)
        elem.send_keys(file_path)
        time.sleep(timeout)  # 页面会执行上传加载一段时间

    @staticmethod
    def file_upload(filepath, browser_type="chrome"):
        """
        文件上传
        :param filepath: 文件路径
        :param browser_type: 浏览器类型
        """
        import win32con
        import win32gui
        try:
            if browser_type == "chrome":
                title = "打开"
            else:
                title = ""
            dialog = win32gui.FindWindow("#32770", title)
            comboboxex32 = win32gui.FindWindowEx(dialog, 0, "comboboxex32", None)
            combobox = win32gui.FindWindowEx(comboboxex32, 0, "combobox", None)
            edit = win32gui.FindWindowEx(combobox, 0, "edit", None)
            button = win32gui.FindWindowEx(dialog, 0, "button", "打开（&0）")
            win32gui.SendMessage(edit, win32con.WM_SETTEXT, None, filepath)
            win32gui.SendMessage(dialog, win32con.WM_COMMAND, 1, button)
        except Exception:
            print("文件上传失败")
            raise

    def is_displayed(self, locator, timeout: int = 3, by='xpath'):
        """
        是否展示在 html dom 里
        """
        time.sleep(0.3)  # 杜绝动作残影
        locator, desc = self._locator_(locator)
        desc = desc + (locator if self.log_locator else '')

        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located((by, locator)))
            flag = '✔ 已加载 '
        except TimeoutException:
            ele = False
            flag = '❕ 没加载 '
        desc = flag + desc
        self.logger.info(desc) if self.logger else print(desc)
        return ele

    def is_visible(self, locator, timeout=6.0, force=False, count=0):
        """
        是否可见，css非隐藏
        """
        time.sleep(0.2)  # 杜绝动作残影
        locator, desc = self._locator_(locator)
        desc = desc + (locator if self.log_locator else '')

        # 可兼容多元素时第一个为隐的情况，后续剔除下面的判断，多元素时自动剔除了无location的
        flag = '✔ 已显示 '
        is_show = True
        eles = self._ele_(locator, 999, timeout=0.2, raise_=False, count=count, logged=False, use_location=False)
        if not eles or (eles and len(eles)) <= 1 or force:  # 为none时、只有一个元素和没有元素时、为force时，需要做显性判断
            flag = '❕ 没显示 '
            if timeout >= 0.5:
                timeout = timeout - 0.5 or 0.2
            try:
                WebDriverWait(self.driver, timeout).until(
                    ec.visibility_of_element_located(('xpath', locator)))
                flag = '✔ 已显示 '
            except TimeoutException:
                is_show = False
                ...

        desc = flag + desc
        self.logger.info(desc) if self.logger else print(desc)
        return is_show

    def js_click(self, locator, index=0, timeout=8, pre_sleep=SLEEP, bac_sleep=SLEEP, raise_=False):
        time.sleep(pre_sleep)
        try:
            elem = self._ele_(locator, index=index, timeout=timeout)
            self.driver.execute_script("arguments[0].click();", elem)
            time.sleep(bac_sleep)
            return elem
        except Exception as e:
            if raise_:
                raise e
            else:
                msg = "点击异常：" + str(e)
                self.logger.error(msg) if self.logger else print(msg)

    def window_scroll(self, width=None, height=None):
        """
        很多方法可以实现
        self.execute_script("var q=document.documentElement.scrollTop=0")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        c = 1
        while True:
            time.sleep(0.02)
            ActionChains(self.driver).send_keys(Keys.UP)
            c += 1
            if c >= 100:
                break
        self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        self.execute_script("var q=document.documentElement.scrollTop=0")
        self.execute_script("var q=document.body.scrollTop=0")
        self.execute_script("var q=document.getElementsByClassName('main')[0].scrollTop=0")
        """
        if height is None:
            self.execute_script("var q=document.body.scrollTop=0")
        else:
            width = "0" if not width else width
            height = "0" if not height else height
            js = "window.scrollTo({w},{h});".format(w=str(width), h=height)
            self.driver.execute_script(js)

    def find_element(self, locator, index=0, raise_=True):
        return self._ele_(locator, index, raise_=raise_)

    def find_elements(self, locator, timeout=3, use_location=False) -> list:
        eles = self._ele_(locator, 999, timeout=timeout, raise_=False, use_location=use_location)
        # 如果有元素，内部会记录，添加一个没元素时的外部记录，没元素时强制记录定位符
        if not eles:
            eles = []
            msg = '❕ 查找元素组 [] %s' % str(locator)
            self.logger.warning(msg) if self.logger else print(msg)
        return eles

    def add_cookies(self, file_path: str):
        """
        通过文件读取cookies
        """
        with open(file_path, "r") as f:
            ck = f.read()
        cookie_list = eval(ck)
        if isinstance(cookie_list, list):
            for cookie in cookie_list:
                self.driver.add_cookie(cookie)
        else:
            raise TypeError("cookies类型错误，它是个列表套字典")

    def save_cookies_to_file(self, file_path: str):
        """
        把cookies保存到文件
        """
        ck = self.driver.get_cookies()
        with open(file_path, 'w') as f:
            f.write(str(ck))

    def set_attribute(self, locator, attribute: str, value, index=0):
        elem = self._ele_(locator, index=index)
        self.driver.execute_script("arguments[0].setAttribute(arguments[1],arguments[2])", elem, attribute, value)

    def alert_is_display(self):
        try:
            return self.driver.switch_to.alert
        except NoAlertPresentException:
            return False

    def stretch(self, size=0.8):
        """
        页面放大/缩小
        :param size: 放大/缩小百分比
        """
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.execute_script(js)

    def release(self):
        ActionChains(self.driver).release().perform()

    def text(self, locator, index=0, timeout=8):
        elem = self._ele_(locator, index, timeout=timeout, interval=False)  # 在批量获取时去掉高亮不然太浪费时间。
        try:
            text = elem.text
        except (StaleElementReferenceException, WebDriverException):
            text = ''
        return text

    def clear(self, locator, index=0):
        """
        清空输入框，清空2次，兼容复杂情况
        """
        elem = self._ele_(locator, index)
        elem.clear()
        time.sleep(0.1)
        return elem.clear()

    def get_attribute(self, name, locator, index=0, raise_=True):
        elem = self._ele_(locator, index, timeout=1, raise_=raise_)
        if elem:
            return elem.get_attribute(name)

    def get_property(self, name, locator, index=0):
        elem = self._ele_(locator, index=index)
        return elem.get_property(name)

    def get_css_property(self, name, locator, index=0, raise_=True):
        elem = self._ele_(locator, index, timeout=1, raise_=raise_)
        return elem.value_of_css_property(name)

    def is_selected(self, locator, index=0):
        """
        可以用来检查 checkbox or radio button 是否被选中
        """
        elem = self._ele_(locator, index)
        if elem:
            return elem.is_selected()
        else:
            return False

    def is_enable(self, locator, index=0, timeout=3, attr='class'):
        """是否可点击，默认+结合属性class值判断"""
        elem = self._ele_(locator, index, timeout=timeout, raise_=False)
        if not elem:
            return False
        dis_flag = ['false', 'disable']
        flag1 = flag2 = flag3 = elem.is_enabled()
        attr_value = elem.get_attribute(attr)
        if attr_value:
            flag2 = all(map(lambda x: x not in attr_value, dis_flag))

        for i in ['/ancestor::button[1]', '/ancestor::li[1]', '/ancestor::span[1]', '/ancestor::div[1]']:
            attr_value2 = self.get_attribute(name='class', locator=self._locator_(locator)[0] + i, raise_=False)
            if attr_value2:
                flag3 = all(map(lambda x: x not in attr_value2, dis_flag))
                if not flag3:
                    break  # 表明已经出现不可点击标志了
        return all([flag1, flag2, flag3])

    def is_clickable(self, locator, index=0, timeout=3, attr='class'):
        return self.is_enable(locator, index=index, timeout=timeout, attr=attr)

    def get(self, uri):
        return self.driver.get(uri)

    def title(self):
        return self.driver.title

    def save_screenshot(self, path, filename=None):
        if not filename:
            filename = datetime.now().strftime('%Y%m%d%H%M%S%f') + '.png'
        file_path = os.path.join(path, filename)
        self.driver.save_screenshot(file_path)

    def current_url(self):
        return self.driver.current_url

    def quit(self):
        quit_ = "✌ ending..."
        self.driver.quit()
        self.driver = None  # 销毁driver
        self.logger.info(quit_) if self.logger else print(quit_)

    def close(self):
        return self.driver.close()

    def maximize_window(self):
        return self.driver.maximize_window()

    @property
    def switch_to(self):
        """
        :Returns:
            - SwitchTo: an object containing all options to switch focus into

        :Usage:
            element = driver.switch_to.active_element
            alert = driver.switch_to.alert
            driver.switch_to.default_content()
            driver.switch_to.frame('frame_name')
            driver.switch_to.frame(1)
            driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
            driver.switch_to.parent_frame()
            driver.switch_to.window('main')
        """
        return self.driver.switch_to

    def back(self):
        """返回历史记录的前一步"""
        return self.driver.back()

    def default_content(self):
        return self.driver.switch_to.default_content()

    def forward(self):
        """前进历史记录的后一步"""
        return self.driver.forward()

    def refresh(self):
        return self.driver.refresh()

    def switch_to_frame(self, frame_reference):
        self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        self.driver.switch_to.parent_frame()

    def window_handles(self):
        return self.driver.window_handles

    def new_window_handle(self):
        return self.window_handles()[-1]

    def switch_to_window(self, handle):
        if isinstance(handle, int):
            handle = self.driver.window_handles[handle]
        self.driver.switch_to.window(handle)

    def dismiss_alert(self):
        self.driver.switch_to.alert.dismiss()

    get_alert_text = property(lambda self: self.driver.switch_to.alert.text, lambda self, v: None)

    def submit(self, locator):
        elem = self._ele_(locator)
        elem.submit()

    def tag_name(self, locator):
        elem = self._ele_(locator)
        return elem.tag_name

    def size(self, locator):
        elem = self._ele_(locator)
        return elem.size

    def move_to_element(self, locator, index=0, timeout=3, click=False, logged=True):
        """鼠标移动到元素上(点击)"""
        elem = self._ele_(locator, index=index, timeout=timeout, logged=logged)
        if click:
            ActionChains(self.driver).move_to_element(elem).click().perform()
        else:
            ActionChains(self.driver).move_to_element(elem).perform()

    def offset_click(self, locator=None, x=0, y=0, **kwargs):
        """坐标（元素偏移）点击"""
        if not x and not y:
            raise ValueError
        click = kwargs.get('click', True)
        double_click = kwargs.get('double_click', False)
        index = kwargs.get('index', 0)
        elem = None
        if locator:
            elem = self._ele_(locator, index=index)
        if elem:
            am = ActionChains(self.driver).move_to_element(elem).move_by_offset(x, y)
        else:
            am = ActionChains(self.driver).move_by_offset(x, y)
        if double_click:
            am.double_click().perform()
        elif click:
            am.click().perform()
        else:
            am.perform()
        ActionChains(self.driver).move_by_offset(-x, -y).perform()  # 抵消累积

    def offset_double_click(self, x=0, y=0, **kwargs):
        self.offset_click(x=x, y=y, **kwargs)
        time.sleep(0.01)
        return self.offset_click(x=x, y=y, **kwargs)

    def hover(self, locator, index=0):
        """悬浮"""
        return self.move_to_element(locator, index=index, click=False)

    def click_and_hold(self, locator, index=0):
        """点击不松"""
        elem = self._ele_(locator, index=index)
        ActionChains(self.driver).click_and_hold(elem).perform()

    def double_click(self, locator, index=0):
        """双击"""
        for i in range(2):
            try:
                elem = self._ele_(locator, index=index)
                return ActionChains(self.driver).double_click(elem).perform()
            except ElementNotInteractableException:
                ...

    def right_click(self, locator, index=0, raise_=True):
        """右键点击"""
        elem = self._ele_(locator, index=index, raise_=raise_)
        ActionChains(self.driver).context_click(elem).perform()
        return elem

    def drag_and_drop(self, source, target, index1=0, index2=0):
        """元素拖拽到元素"""
        elem1 = self._ele_(source, index=index1)
        elem2 = self._ele_(target, index=index2)
        ActionChains(self.driver).drag_and_drop(elem1, elem2).perform()

    def drag_and_drop_by_offset(self, locator, x, y, index=0, return_=False):
        """元素拖拽至坐标，full_screen t"""
        elem = self._ele_(locator=locator, index=index)
        try:
            ActionChains(self.driver).drag_and_drop_by_offset(elem, xoffset=x, yoffset=y).perform()
        except (ElementNotInteractableException, MoveTargetOutOfBoundsException):
            if return_:
                return 'over'  # 滚到头了
            try:
                x = x * 0.66 if x else x
                y = y * 0.66 if y else y
                ActionChains(self.driver).drag_and_drop_by_offset(elem, xoffset=x, yoffset=y).perform()
            except (ElementNotInteractableException, MoveTargetOutOfBoundsException):
                ...  # 还滚动不了就算了，无需报错

    @staticmethod
    def select_by_value(elem, value):
        Select(elem).select_by_value(value)

    @staticmethod
    def select_by_index(elem, index):
        Select(elem).select_by_index(index)

    @staticmethod
    def select_by_visible_text(elem, text):
        Select(elem).select_by_visible_text(text)

    def location_once_scrolled_into_view(self, locator, index=0, raise_=True):
        """滚动到元素，竖向滚动更好用，横向滚动建议用drag"""
        time.sleep(0.1)
        elem = self._ele_(locator, index=index, raise_=raise_)
        if not raise_ and not elem:
            return
        try:
            elem_view = elem.location_once_scrolled_into_view
        except WebDriverException as e:
            msg = 'location_once_scrolled_into_view报错' + str(e)[:10] + '...'
            self.logger.info(msg) if self.logger else print(msg)
            return
        time.sleep(0.1)
        return elem_view

    def scroll_views(self, locators, tar_locator, sep=5, **kwargs):
        """
        于元素组中滚动至目标元素出现
        """
        tar_index = kwargs.get('tar_index', 0)
        n = kwargs.get('n', 0)
        if n >= 2:
            return False
        eles = self.find_elements(locators)
        if not len(eles) >= sep:
            sep = 1
        for i in range(0, len(eles) - 1, sep):
            if self.is_visible(tar_locator, 0.5):
                self.location_once_scrolled_into_view(tar_locator, index=tar_index)
                # time.sleep(0.3)
                return True
            else:
                self.location_once_scrolled_into_view(eles[i])
        else:  # 若滚动完了还没有，则需要重新获取
            return self.scroll_views(locators, tar_locator, sep, tar_index=tar_index, n=n + 1)

    def scroll_to_fill(self, locators, tar_locator, tar_value, **kwargs):
        """滚动至目标输入框然后填值"""
        sep = kwargs.get('sep', 10)
        n = kwargs.get('n', 0)
        if self.scroll_views(locators=locators, tar_locator=tar_locator, sep=sep, n=n):
            return self.send_keys(tar_locator, tar_value)

    def drag_bar_to_show(self, tar_locator, bar_locator, bar_index=0, direction=1, pixel=100):
        """拖动+滚动直至目标元素出现
        如果元素滑过去了，is_visible是通过的，但看不见。要想看见，上下的用scroll_view，左右的靠拖拽
        scroll_view在上下滚动至可见元素时，滚动的隐藏范围更大，左右滚动时范围较小。
        """
        x, y = 0, pixel
        if not direction:
            x, y = y, x
        for i in range(10):
            if self.drag_and_drop_by_offset(locator=bar_locator, x=x, y=y, index=bar_index, return_=True):
                break
            if self.is_visible(locator=tar_locator, timeout=0.5):
                self.location_once_scrolled_into_view(locator=tar_locator)
                break

    def execute_script(self, js, *args):
        return self.driver.execute_script(js, *args)

    def enter(self, locator, index=0):
        elem = self._ele_(locator, index=index)
        elem.send_keys(Keys.ENTER)

    def select_all(self, locator, index=0):
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "a")
        else:
            elem.send_keys(Keys.CONTROL, "a")

    def cut(self, locator, index=0):
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "x")
        else:
            elem.send_keys(Keys.CONTROL, "x")

    def copy(self, locator, index=0):
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "c")
        else:
            elem.send_keys(Keys.CONTROL, "c")

    def paste(self, locator, index=0):
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "v")
        else:
            elem.send_keys(Keys.CONTROL, "v")

    def backspace(self, locator, empty: bool = True):
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.BACKSPACE)

    def delete(self, locator, empty: bool = True):
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.DELETE)

    def tab(self, locator):
        elem = self._ele_(locator)
        elem.send_keys(Keys.TAB)

    def space(self, locator):
        elem = self._ele_(locator)
        elem.send_keys(Keys.SPACE)

    def esc(self):
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def press(self, key: str):
        if key.upper() not in Keys.__dict__.keys():
            raise ValueError
        ActionChains(self.driver).send_keys(Keys.__dict__[key.upper()]).perform()

    # 操作的中文，方便日志打印
    __operate__ = lambda self: {
        'click': '点击 ',
        'send_keys': '输入 ',
        'double_click': '双击 ',
        'js_click': 'js点击 ',
        'drag_and_drop': '拖拽 ',
        'right_click': '右键点击 ',
        'find_element': '查找元素 ',
        'find_elements': '查找元素组 ',
        'get_attribute': '获取属性 ',
        'set_attribute': '设置属性 ',
        'text': '元素文本 ',
        'move_to_element': '鼠标移到 ',
        'location_once_scrolled_into_view': '滚动到 ',
        'drag_and_drop_by_offset': '拖拽 ',
        'is_selected': '是否选中 ',
    }

    @staticmethod
    def __get_locator_future__(locator):
        """获取元素自带的文本特征"""
        res = re.findall(r"text\(\)\.*.*?]", locator) or re.findall(r"holder\.*.*?]", locator)
        desc = locator
        if res:
            res = res[-1]
            try:
                text = res.index('text()')
            except ValueError:
                text = res.index('holder')

            if '"' in res and "'" in res:
                r1 = res.rindex("'")
                r2 = res.rindex("'")
                r = min([r1, r2])
            elif "'" in res:
                r = res.rindex("'")
            elif '"' in res:
                r = res.rindex('"')
            else:  # 说明只有这个属性没有值
                r = -1
            desc = res[text + 8:r]
        return desc

    def input_set_value(self, loc, value):
        """
        往input框塞值（部分情况下sendkeys无效）
        :param loc: 元素定位
        :param value: 输入的值
        """
        ele = self.driver.find_element(by=By.XPATH, value=loc)
        actions = ActionChains(self.driver)
        actions.move_to_element(ele).click(ele).perform()
        self.driver.switch_to.active_element.send_keys(Keys.CONTROL, "a")
        self.driver.switch_to.active_element.send_keys(value, Keys.ENTER)

    @staticmethod
    def get_current_year():
        """获取当前年份"""
        return time.strftime("%Y", time.localtime())

    def new_tab(self, to=True):
        self.driver.execute_script('window.open("","_blank");')
        if to:
            self.switch_to_window(handle=-1)


def overtime(timeout):
    def _overtime(func):
        return wraps(func)(lambda *args, **kwargs: _overtime_(timeout, func, args=args, arg2=kwargs))

    def _overtime_(_timeout, func, args=(), arg2=None):
        if not arg2:
            arg2 = {}
        if not args:
            args = ()

        ret = []
        exception = []
        is_stopped = False

        def funcwrap(args2, kwargs2):
            try:
                ret.append(func(*args2, **kwargs2))
            except TimeoutError:
                pass
            except Exception as e:
                exc_info = sys.exc_info()
                if is_stopped is False:
                    e.__traceback__ = exc_info[2].tb_next
                    exception.append(e)

        thread = StoppableThread(target=funcwrap, args=(args, arg2))
        thread.daemon = True

        thread.start()
        thread.join(_timeout)

        if thread.is_alive():
            is_stopped = True
            thread.stop_thread(TimeoutError)
            thread.join(min(.1, _timeout / 50.0))
            raise TimeoutError('Out of %s seconds' % _timeout)
        else:
            thread.join(.5)
        if exception:
            raise exception[0] from None
        if ret:
            return ret[0]

    class StoppableThread(threading.Thread):
        def stop_thread(self, exception, raise_every=2.0):
            if self.is_alive() is False:
                return True
            self._stderr = open(os.devnull, 'w')
            jt = JoinThread(self, exception, repeat_every=raise_every)
            jt._stderr = self._stderr
            jt.start()
            jt._stderr = self._stderr

    class JoinThread(threading.Thread):
        def __init__(self, other_thread, exception, repeat_every=2.0):
            threading.Thread.__init__(self)
            self.otherThread = other_thread
            self.exception = exception
            self.repeatEvery = repeat_every
            self.daemon = True

        def run(self):
            self.otherThread._Thread__stderr = self._stderr
            while self.otherThread.is_alive():
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.otherThread.ident),
                                                           ctypes.py_object(self.exception))
                self.otherThread.join(self.repeatEvery)
            try:
                self._stderr.close()
            except:
                ...

    return _overtime


class _Win32:
    """
    对两个find增加耗时处理，sendmessage不用增加耗时处理
    """

    def __init__(self, win32gui, win32con):
        self.win32gui = win32gui
        self.win32con = win32con

    def find_window(self, class_, title, n: int = 5):
        """
        原生FindWindow很容易出现找不到的情况，以此来避免
        """
        time.sleep(0.2)
        while n:
            n -= 1
            try:
                handle_id = self.win32gui.FindWindow(class_, title)
            except:
                handle_id = 0
            if not handle_id:
                time.sleep(0.2)
                return self.find_window(class_, title, n)
            return handle_id

    def find_window_ex(self, dialog, m, class_, text, n: int = 5):
        """
        原生FindWindowEx很容易出现找不到的情况，以此来避免
        """
        time.sleep(0.2)
        while n:
            n -= 1
            try:
                handle_id = self.win32gui.FindWindowEx(dialog, m, class_, text)
            except:
                handle_id = 0
            if not handle_id:
                time.sleep(0.2)
                return self.find_window_ex(dialog, m, class_, text, n)
            return handle_id


BROWSER = 'chrome'


class upload:
    """
    winspy工具识别到win的窗口位置，点击Tree展开所在的层级，通过识别外围一步一步向下传递.
    每个步骤之间要考虑延时
    可代替autoit调用工具的形式，更加pythonic。
    无界面上传只能通过send_keys和playwright的send_files了。

    包括以下的情况：
    1. 窗口不存在直接结束
    2. 文件地址为空直接结束
    3. 没有此文件，要取消上传
    4. 一上来就是‘找不到’的窗口，要去掉该窗口，再上传
    5. 文件和窗口正常，正常上传
    """

    def __enter__(self):
        self.close_if_opened()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

    def __init__(self, win32gui, win32con):
        self.__title__ = self.__get_title()
        print(self.__title__)
        assert self.__title__
        self.__win32gui = win32gui
        self.__win32con = win32con
        self.__win32 = _Win32(win32gui, win32con)

    def close_if_opened(self):
        """
        如果点击之前就有弹窗，说明是上一次的弹窗，会影响接下来的操作，需要关掉。
        这是系统级的判断，如果另一个浏览器打开了窗口，可能把那个关了。
        如果能保证一个电脑同时只有一个浏览器在上传，那可以用。
        担有极少数的场景是：多个谷歌浏览器在同时上传，那么就没办法了。
        包括uploads方法也是，如果有另一个浏览器打开了‘打开’窗口，那填充的值跑到另一个浏览器上去了。
        至于autoit，更别提了。
        优先使用原生的send_keys、fill等；如果不行再用uploads+此方法结合；如果有多个浏览器上传不要用这个方法。
        ups.close_if_opened
        page.click('//button')
        ups.upload
        """
        dialog = self._dialog(n=1)
        if dialog:
            return self.__cancel(dialog)

    def doing(self, file_path: str, timeout: float = 6):
        """
        上传动作（触发的动作不要放到这个库里，上传不了是点击的元素本身有问题，要用js点有的js点了也没反应）
        :param file_path: 上传的文件地址
        # :param browser_type: 浏览器类型
        :param timeout: 等待时间
        """
        # 此对象在‘打开’窗口 和‘文件不存在’窗口可复用
        dialog = self._dialog()

        if not dialog:
            print("'打开' 窗口不存在")
            return False  # 说明点击有问题，给false的意思是让外部再触发一次。

        if not file_path:
            print("文件名为空，取消上传")
            self.__cancel(dialog)
            return True  # 文件名为空，不是点击问题，不需要外部再触发。

        self.__occur_no_exist(n=1)  # 如果一开始/上传过某些文件之后，出现‘找不到窗口’，需要关闭这个窗口，这里不管你是否出现，我都要填写，所以没必要搞个对象接收

        return self.__fill_and_open(file_path, timeout - 1)

    @staticmethod
    def __get_title():
        brs = BROWSER.lower()
        title = "打开" if brs in ["chrome", 'edge'] else "文件上传" if brs == "firefox" else False
        return title if title else print("建议用谷歌浏览器噢")  # 利用 print 返回的是None

    def _dialog(self, n=2):
        """定位一级窗口"#32770"-"打开"，参数1-class的值；参数2-title的值"""
        dialog = self.__win32.find_window("#32770", self.__title__, n=n)
        return dialog if dialog else False

    def __cancel(self, dialog):
        """对打开的窗口做‘取消’处理"""

        # 参数1-父窗口对象；参数2未知一般为None；参数3-子窗口类名；参数4-子窗口的text值
        # ‘取消’的布局在chrome和firefox一致
        cancel = self.__win32.find_window_ex(dialog, 0, 'Button', "取消")

        # 参数1-窗口句柄，参数2-消息类型；参数3-文本大小；参数4-存储位置
        # 点击取消为什么不能用点击’打开‘那种方式，kb
        self.__win32gui.SendMessage(cancel, self.__win32con.WM_LBUTTONDOWN, 0, 0)
        self.__win32gui.SendMessage(cancel, self.__win32con.WM_LBUTTONUP, 0, 0)
        return False

    def __occur_no_exist(self, n=3):
        """
        出现“找不到文件”的窗口，需要点’确定‘。
        细节：此时文件路径变为最后结尾处的文件名，这里曾影响我判断过。
        """
        # 除了self.__title__其它布局在chrome和firefox一致
        new_dialog = self.__win32.find_window("#32770", self.__title__, n=n)
        sure1 = self.__win32.find_window_ex(new_dialog, 0, 'DirectUIHWND', None, n=n)
        if not sure1:
            return False

        sure2 = self.__win32.find_window_ex(sure1, 0, 'CtrlNotifySink', None, n=n)
        sure3 = self.__win32.find_window_ex(sure2, 0, 'Button', '确定')
        self.__win32gui.SendMessage(new_dialog, self.__win32con.WM_COMMAND, 1, sure3)
        return True

    def __fill_and_open(self, file_path, delay):
        """定位 “文件名(N):” 后面的编辑框所在的位置，点击打开"""
        # 输入框的布局在chrome和firefox一致
        dialog = self.__win32.find_window("#32770", self.__title__)
        edit_out2 = self.__win32.find_window_ex(dialog, 0, "ComboBoxEx32", None)
        edit_out1 = self.__win32.find_window_ex(edit_out2, 0, "ComboBox", None)
        edit = self.__win32.find_window_ex(edit_out1, 0, "Edit", None)

        # 发送文件路径
        self.__win32gui.SendMessage(edit, self.__win32con.WM_SETTEXT, None, file_path)
        time.sleep(0.2)

        # 定位‘打开’，布局在chrome和firefox一致
        open_button = self.__win32.find_window_ex(dialog, 0, 'Button', "打开(&O)")

        # 点击打开
        @overtime(1)
        def _click_open():
            self.__win32gui.SendMessage(dialog, self.__win32con.WM_COMMAND, 1, open_button)

        try:
            _click_open()
        except TimeoutError:
            print("不存在该文件，点击打开按钮超时")
            self.__occur_no_exist()
            self.__cancel(dialog)
            return False
        # 判断是不是出现了‘找不到文件‘的窗口
        if self.__occur_no_exist():
            self.__cancel(dialog)
            return False
        else:
            if delay >= 2:
                delay = delay - 2
            time.sleep(delay)
            return True


class Utils:
    cur_time = property(lambda self: datetime.now().strftime('%Y%m%d%H%M%S%f'))

    get_file_date = lambda self, file_path: datetime.fromtimestamp(os.stat(file_path).st_mtime)

    sorted_file_by_time = lambda self, dir_path, reverse=True: [
        os.path.join(dir_path, x[0]) for x in sorted([
            (file, self.get_file_date(os.path.join(dir_path, file))) for file in os.listdir(dir_path)
        ], key=lambda x: x[1], reverse=reverse)
    ]

    def preset(self, dir_path):
        """输出文件夹清理 + 报告备份"""
        report_md5 = []
        recent_report_path = None
        for i in os.listdir(dir_path):
            i_path = os.path.join(dir_path, i)
            if '.' in i:
                os.remove(i_path)
            if 'report' in i:
                if 'report' != i:
                    report_md5.append(self.get_file_md5(os.path.join(i_path, 'report.html')))
                else:
                    recent_report_path = i_path
        recent_html = os.path.join(recent_report_path, 'report.html')
        if not os.path.exists(recent_html):
            return
        recent_report_md5 = self.get_file_md5(recent_html)
        if recent_report_md5 not in report_md5:
            bake_report_path = os.path.join(dir_path, 'report' + self.cur_time[4:-6])
            shutil.copytree(recent_report_path, bake_report_path)
        self.clear_by_mtime(dir_path)

    @staticmethod
    def get_file_md5(file_path):
        """获取文件md5值"""
        m = md5()
        with open(file_path, 'rb') as f:
            while ...:
                data = f.read()
                if not data:
                    break
                m.update(data)
        return m.hexdigest()

    @staticmethod
    def clear_by_mtime(dir_path, days=4):
        files_date = [(file, datetime.fromtimestamp(os.stat(os.path.join(dir_path, file)).st_mtime))
                      for file in os.listdir(dir_path)]
        sorted_file = [(os.path.join(dir_path, x[0]), x[1]) for x in
                       sorted(files_date, key=lambda x: x[1], reverse=True)]
        for i in sorted_file:
            file, date = i
            if date < datetime.today() - timedelta(days=days):
                os.remove(file)

    @staticmethod
    def clear_by_type(dir_path, end='.jpg'):
        for i in [os.path.join(dir_path, i) for i in os.listdir(dir_path)]:
            if i.endswith(end):
                os.remove(i)
