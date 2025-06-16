import shutil
from datetime import datetime, timedelta
import platform
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, \
    StaleElementReferenceException, TimeoutException, ElementNotInteractableException, InvalidSelectorException, \
    MoveTargetOutOfBoundsException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
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
import win32con
import win32gui

BROWSER = 'chrome'


class WebDriver:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'  # 兼容 robot framework
    SLEEP = 0  # 前后置等待初始时间（0.1~0.5）
    FLASH_CT = 1  # 为1很好，亮一次即可；除非演示或需要高亮可置为2

    def __init__(
            self,
            executable_path: str = '',
            display: bool = True,
            logger=None,
            log_locator: bool = False,
            remote_location: str = '',
            caption: bool = False,
            options: list = '',
            experimental_option: dict = ''
    ):
        """
        :param executable_path: 驱动路径
        :param display: 是否以界面方式显示
        :param logger: 日志对象（最好是 pytest-loguru）
        :param log_locator: 是否记录 定位表达式
        :param remote_location: grid状态下从机的浏览器路径
        :param caption: 字幕
        :param options: 设置项，例如:
            '--headless'
            '--no-sandbox'
            '--disable-gpu'
            '--disable-dev-shm-usage'
            'window-size=1920x1080'
            'blink-settings=imagesEnabled=False'
            'user-agent="MQQBrowser/26 Mozilla/5.0 ..."'
            'user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'
            "--unsafely-treat-insecure-origin-as-secure=http://192.168.90.26:7050"  # 允许不安全的下载这一条才是起作用的
        :param experimental_option: 特殊设置项，例如: 不加载图、取消弹窗询问、设置下载路径
            prefs =
            {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.popups': 0,
            'download.default_directory': r'd:\'
            "download_restriction": 0,  # 禁用下载保护
            "safebrowsing.enabled": True  # 允许不安全的下载
            }
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
        self.remote_location = remote_location
        if remote_location:
            self.executable_path = remote_location[remote_location.rindex(os.sep) + 1:remote_location.rindex('.')]
        self.caption = caption

    def open_browser(self):
        """打开浏览器，默认打开谷歌"""
        executable_path = self.executable_path.lower()
        global BROWSER
        if 'chrome' in executable_path or not executable_path:  # 默认没用时用谷歌浏览器
            browser_type = 'chrome'
            opt = ChromeOptions()
            for i in self.options:
                opt.add_argument(i)
            for i in [
                "--disable-infobars", "--disable-extensions", "--disable-popup-blocking",  # 去掉弹窗
                "--allow-running-insecure-content", "--disable-web-security",
            ]:
                opt.add_argument(i)

            if self.experimental_option:
                for k, v in self.experimental_option.items():
                    opt.add_experimental_option(k, v)
            opt.add_experimental_option('excludeSwitches', ['enable-logging', ])  # 避免usb打印错误
        elif 'gecko' in executable_path or 'firefox' in executable_path:
            browser_type = 'firefox'
            BROWSER = browser_type
            opt = FirefoxOptions()
            # 火狐不能这样配否则报错
            # if self.experimental_option:
            #     for k, v in self.experimental_option.items():
            #         opt.set_preference(k, v)
        elif 'edge' in executable_path:
            browser_type = 'edge'
            BROWSER = browser_type
            opt = EdgeOptions()
        else:
            raise ValueError
        opt.set_capability('pageLoadStrategy', 'normal')
        opt.binary_location = self.remote_location
        exist_driver = True
        if not os.path.exists(executable_path) or not executable_path:
            msg = '❕ chromedriver路径不存在，正在下载中...'
            self.logger.info(msg) if self.logger else print(msg)
            exist_driver = False  # 有的放在python目录下就无需配置

        # grid方式：必须可见，内部通过option对象区分浏览器类型
        remote_url = 'http://localhost:4444/wd/hub'
        if self.remote_location:
            msg = "✔ grid启动：" + remote_url
            self.logger.info(msg) if self.logger else print(msg)
            try:
                self.driver = webdriver.Remote(command_executor=remote_url, options=opt)
                self.driver.maximize_window()
            except Exception as e:
                msg = "✘ grid远程失败，请检查url、opt"
                self.logger.info(msg) if self.logger else print(msg)
                raise e
        else:
            try:
                if platform.system().lower() in ["windows", "macos"] and self.display:
                    if browser_type == 'chrome':
                        from selenium.webdriver.chrome.service import Service
                        self.driver = webdriver.Chrome(options=opt, service=Service(
                            executable_path=executable_path if exist_driver else None))
                    elif browser_type == 'firefox':
                        from selenium.webdriver.firefox.service import Service
                        opt.binary = FirefoxBinary()  # 当前版本的得保留这一句
                        # 火狐的option外部经常配置错误，固去掉
                        self.driver = webdriver.Firefox(service=Service(
                            executable_path=executable_path if exist_driver else None, log_path=os.devnull,
                            log_output=os.devnull))
                    elif browser_type == 'edge':
                        from selenium.webdriver.edge.service import Service
                        self.driver = webdriver.Edge(options=opt, service=Service(
                            executable_path=executable_path if exist_driver else None))
                    else:
                        raise ValueError
                    self.driver.maximize_window()
                    msg = '✔ 打开浏览器'
                    self.logger.info(msg) if self.logger else print(msg)

                else:  # 无界面方式/流水线
                    for i in ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']:
                        opt.add_argument(i)
                    if browser_type == 'chrome':
                        self.driver = webdriver.Chrome(options=opt)
                    else:
                        self.driver = webdriver.Firefox(options=opt)
                    self.driver.maximize_window()
                time.sleep(1)  # 有user-dir的时候最好等待一下
            except WebDriverException as e:
                raise e
        global g_driver
        g_driver = self.driver
        return self.driver

    def __highlight__(self, ele, count=FLASH_CT):
        """高亮"""
        if count is None:
            count = self.FLASH_CT
        if count < 0:  # 为0时闪的很快，不会间隔闪烁，为-1表示不希望高亮
            return
        js = 'arguments[0].style.border='
        js2 = 'arguments[0].style.outline='  # 不占据空间但有的不亮
        """
        好看的色码：红色-#FF0000；海蓝-#70DB93;黄色-#FFFF00；淡紫色-#DB7093；青色-#00FFFF；天蓝-#38B0DE
        """
        if self.display:
            interval = 0.01
            try:
                for _ in range(count):
                    self.driver.execute_script(js + '"2px solid #FF0000"', ele)
                    self.driver.execute_script(js2 + '"2px solid #FF0000"', ele)
                    time.sleep(interval)
                    self.driver.execute_script(js + '"2px solid #FFFF00"', ele)
                    self.driver.execute_script(js2 + '"2px solid #FFFF00"', ele)
                    time.sleep(interval)
                self.driver.execute_script(js + '"2px solid #FF0000"', ele)
                self.driver.execute_script(js2 + '"2px solid #FF0000"', ele)
                time.sleep(interval)
                if count:
                    time.sleep(interval * 3)
                self.driver.execute_script(js + '""', ele)
                self.driver.execute_script(js2 + '""', ele)
            except WebDriverException:
                ...

    def __fe__(self, by, locator_, timeout):
        """查找元素组实现"""

        @overtime(timeout)
        def fe():
            self.driver.find_elements(by=by, value=locator_)
            time.sleep(0.05)
            return self.driver.find_elements(by=by, value=locator_)

        eles = fe()[:100]
        for i in eles:
            try:
                i
            except StaleElementReferenceException as e:
                raise e
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
        """查找元素"""
        y = timeout % 1
        interval = [1.0 for _ in range(int(timeout))]
        if y:
            interval.append(y)
        use_location = kwargs.get('use_location', True)
        raise_ = kwargs.get('raise_', True)
        self.__pre_force_sleep__(locator=locator_)
        try:
            for _ in interval:
                try:
                    elems = self.__fe__('xpath', locator_, _)
                except TimeoutError:
                    continue  # TimeoutError里面已经耗时过了，这里无需再sleep
                except (InvalidSelectorException, StaleElementReferenceException):
                    time.sleep(0.66)  # 这两个不知道会耗时多少，取6
                    continue
                if not elems:
                    time.sleep(0.66)
                    continue
                # 数据清洗
                count = kwargs.get('count')  # 虽然这里没给，但里面有判断
                if index == 999:  # 999为元素列表
                    elem = elems
                    if len(elem) == 1:  # 给is_visible留的多元素的1个时也亮
                        self.__highlight__(elem[0], count=count)
                elif not index and len(elems) > 1 and use_location:  # 无索引且有多个元素时，-1时不用清洗
                    elem = self._filter_(elems)
                    if not elem:
                        time.sleep(0.66)
                        continue
                    elem = elem[0]
                else:  # 有索引的
                    elem = elems[index]
                    self.__highlight__(elem, count=count)
                return elem
        except Exception as e:
            if raise_:
                raise e

    def _locator_(self, locator, vague=False):
        """返回 真实locator，描述，是否为Web对象"""
        if isinstance(locator, WebElement):
            return locator, ''
        elif isinstance(locator, tuple):
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
                if '|' in locator:  # 非xpath也能这样写了
                    ls = locator.split('|')
                    real_ls = ''
                    for i in ls:
                        i = i.strip()
                        real_ls += "//*[text()='{0}']".format(i) + '|'
                    real_locator = real_ls.rstrip('|')
                else:
                    real_locator = "//*[text()='{0}']".format(locator)
                if vague:
                    real_locator = "//*[contains(text(),'{0}')]".format(locator)
        else:
            raise TypeError
        return real_locator, desc

    def _ele_(self, locator, index=0, timeout=8.0, **kwargs):
        """
        元素处理
        """
        if isinstance(locator, WebElement):
            if index == 999:
                return [locator]
            return locator
        vague = kwargs.get('vague', False)
        logged = kwargs.get('logged', True)
        raise_ = kwargs.get('raise_', True)
        pre_sleep = kwargs.get('pre_sleep', 0.01)  # 0.01也很关键
        time.sleep(pre_sleep)
        locator, desc = self._locator_(locator, vague=vague)

        # 获取描述（有反射机制莫再封，反射机制只针对当前文件对它的引用）
        try:
            func = inspect.stack()[1].function
        except IndexError:
            func = 'find_elements'
        desc = self.__operate__().get(func, '') + desc
        if self.log_locator:
            desc = desc + ' ' + locator
        ele = self.__find_ele(locator_=locator, index=index, timeout=timeout, **kwargs)
        if ele:
            if logged:  # send_keys 无需记录因其外层有记录
                msg = "✔ %s" % (desc if desc else locator)
                self.logger.info(msg) if self.logger else print(msg)
                if self.caption:
                    Utils.caption(msg=msg)
            return ele
        else:
            if not raise_:  # 指定不抛出异常时也无需记录
                logged = False
            if logged:
                msg = "✘ %s" % desc if desc else locator
                self.logger.error(msg) if self.logger else print(msg)
            if raise_:
                raise ValueError("没找到元素 %s, 请检查表达式" % locator)

    def click(self, locator, index: int = 0, timeout=8, **kwargs):
        """
        点击元素
        关于sleep：前后加起来0.1秒，提升页面加载容错性，视觉停留只是其次，0.05是最低最合适的值
        """
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        bac_sleep = kwargs.get('bac_sleep', self.SLEEP)
        raise_ = kwargs.get('raise_', True)
        vague = kwargs.get('vague', False)
        time.sleep(pre_sleep)
        elem = self._ele_(locator, index, timeout, raise_=raise_, vague=vague)
        try:
            elem.click()
        except Exception as e:
            try:
                # 强制点击-不可穿透遮罩层（手动鼠标形式点击），可解决ElementClickInterceptedException; StaleElement
                self.ac_click(locator, index=index)
            except Exception as e2:
                try:
                    # 可以穿透遮罩层，可解决ElementClickInterceptedException
                    self.driver.execute_script("arguments[0].click();", elem)
                except Exception as e3:
                    if raise_:
                        raise e3
                    else:
                        msg = '✘ 点击失败 %s' % (
                                str(locator) + str(e3)[:10] + '...' + str(e)[:10] + '...' + str(e2)[:10]
                        )
                        self.logger.error(msg) if self.logger else print(msg)
        self.__bac_force_sleep__(locator, sleep=bac_sleep)
        return elem

    def click_if_visible(self, locator, timeout=6, bac_sleep=0):
        """
        如果出现了目标元素就点击，该方法仅适用于索引0、-1、中间的情况，其它情况索引请放在xpath里
        """
        locator = self.is_visible(locator=locator, timeout=timeout)
        if not locator:
            return
        return self.click(locator=locator, timeout=1, bac_sleep=bac_sleep)

    def __pre_force_sleep__(self, locator, sleep=0):
        """前置强制等待情况：查找iframe之前"""
        if self.caption:  # 字幕是串行的，无需等待
            return
        time.sleep(sleep)
        try:
            locator, _ = self._locator_(locator)
        except TypeError:
            return
        if 'iframe' in locator:
            time.sleep(1)

    def __bac_force_sleep__(self, locator, sleep: float = 0):
        """后置强制等待情况：增删改查事务之后"""
        if not isinstance(locator, str):
            time.sleep(0.1)
            return
        if self.caption:
            return
        time.sleep(sleep)
        try:
            locator, _ = self._locator_(locator)
        except TypeError:  # 有时传进来的是webelement对象
            return
        kw = locator.rfind('=') + 2
        if locator[kw:kw + 1] in ['确', '是', '搜', '创', '新']:
            time.sleep(1)  # 一般点完确定后会有个加载过程

    def ac_click(self, locator, index=0):
        """鼠标点击"""
        return self.move_to_element(locator=locator, index=index, click=True)

    def send_keys(self, locator, value, index: int = 0, timeout: int = 6, clear: bool = True, enter=False, **kwargs):
        """
        输入框输入值，上传请用upload方法
        clear：输入前是否清空
        enter：输入后是否回车
        """
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        bac_sleep = kwargs.get('bac_sleep', 0.5)
        active = kwargs.get('active', False)  # 是否为活动元素输入，针对非常规输入框需要点一下激活再输入

        if not value and value != 0:  # 0可以有
            return
        time.sleep(pre_sleep)

        def normal_send():
            elem = self._ele_(locator, index, timeout, raise_=False, logged=False)
            if not elem:
                return False
            if clear:
                try:
                    self.clear(locator=locator, index=index)
                except Exception as e1:
                    try:
                        elem.send_keys(Keys.CONTROL, "a")
                    except Exception as e2:
                        msgf = "❕ clear失败-无妨" + str(e1)[-1] + "全选删除失败-无妨" + str(e2)
                        self.logger.error(msgf) if self.logger else print(msgf)  # 清空失败不抛出仅记录
            try:
                elem.send_keys(value)
                self.logger.info(msg) if self.logger else print(msg)
                if self.caption:
                    Utils.caption(msg=msg)
                if enter:
                    time.sleep(0.1)  # 有一些需要预加载否则直接enter没反应过来
                    elem.send_keys(Keys.ENTER)
            except Exception:
                return False
            self.__bac_force_sleep__(locator, sleep=bac_sleep / 2)
            return True

        def active_send():
            """当前活动元素输入值"""
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
                if self.caption:
                    Utils.caption(msg=msg)
            except Exception as e:
                msg1 = '✘ 输入方式2也失败' + str(e)[9:38] + '...'
                self.logger.warning(msg1) if self.logger else print(msg1)
                return False
            self.__bac_force_sleep__(locator)
            return True
        locator_, desc = self._locator_(locator)
        msg = '✔ 输入 ' + desc + ' ' + str(value)
        if not locator or active:
            return active_send()
        if not normal_send():
            return active_send()

    def upload(self, locator, file_path: str, index=0, timeout=6):
        """
        通过输入值的形式上传，内部还是send_keys，处理windows弹窗上传请用uploads库
        """
        elem = self._ele_(locator, index=index, timeout=timeout * 0.8)
        elem.send_keys(file_path)
        time.sleep(timeout * 0.7)  # 页面会执行上传加载一段时间

    @staticmethod
    def upload_by_win32(file_path: str, timeout=6):
        """通过窗口的形式上传，很完美，无需再调ups"""
        ups = upload()
        ups.doing(file_path=file_path, timeout=timeout)
        ups.close_if_opened()

    def is_displayed(self, locator, timeout: int = 3):
        """
        是否展示在 html dom 里
        """
        if isinstance(locator, WebElement):
            return True
        time.sleep(0.5)  # 杜绝动作残影

        locator, desc = self._locator_(locator)
        desc = self._desc_(locator=locator, desc=desc)

        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located(('xpath', locator)))
            flag = '✔ 已加载 '
        except TimeoutException:
            ele = False
            flag = '❕ 没加载 '
        msg = flag + desc
        self.logger.info(msg) if self.logger else print(msg)
        if self.caption:
            Utils.caption(msg=msg)
        return ele

    def _desc_(self, locator, desc):
        """描述"""
        if isinstance(locator, WebElement):
            locator = '$当前对象'
        return desc + locator if self.log_locator else desc

    def is_visible(self, locator, timeout=6.0, **kwargs) -> bool:
        """
        是否可见：多元素判断+兼容原生；
        多元素情况值判断索引为0、-1、中间
        """
        if isinstance(locator, WebElement):
            return True
        used = 0
        if timeout > 1:
            time.sleep(0.5)  # 杜绝页面残影，若小于1秒说明不希望时间浪费，必须为0.5勿改
            used = 0.5
        locator, desc = self._locator_(locator)
        desc = self._desc_(locator=locator, desc=desc)

        # 目的：多元素时兼容
        count = kwargs.get('count', 0)  # 为0表示该方法快速亮一下即可
        eles = self._ele_(locator, 999, timeout=0.5, raise_=False, count=count, logged=False, use_location=True)
        if isinstance(eles, list) and len(eles) > 1:
            desc = '元素组-' + desc
        timeout = timeout - used - 0.5
        if '元素组' in desc:  # 是为后面的兼容扣除
            timeout = timeout - 1
        if timeout <= 0:
            timeout = 0.25

        is_show = False
        flag = '❕ 没显示 '
        try:
            WebDriverWait(self.driver, timeout).until(
                ec.visibility_of_element_located(('xpath', locator)))  # 它只支持单元素多元素时默认第一个
            is_show = locator
            flag = '✔ 已显示 '
        except TimeoutException:
            if '元素组' in desc:
                l_locator = "(" + locator + ")[last()]"  # 多元素时，最贴近当前操作的元素是最后一个，要兼容这种情况
                try:
                    WebDriverWait(self.driver, 0.5).until(
                        ec.visibility_of_element_located(('xpath', l_locator)))
                    is_show = locator
                    flag = '✔ 已显示-最后一个元素 '
                except TimeoutException:
                    mid = int((len(eles) + 1) / 2)
                    mid_locator = f"(" + locator + f")[{mid}]"
                    try:
                        WebDriverWait(self.driver, 0.5).until(
                            ec.visibility_of_element_located(('xpath', mid_locator)))  # 多元素时，兼容中间的情况
                        is_show = locator
                        flag = '✔ 已显示-中间元素 '
                    except TimeoutException:
                        ...
        desc = flag + desc
        self.logger.info(desc) if self.logger else print(desc)
        if self.caption:
            Utils.caption(msg=desc)
        return is_show

    def js_click(self, locator, index=0, timeout=8, **kwargs):
        """
        以js的形式点击
        """
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        bac_sleep = kwargs.get('bac_sleep', self.SLEEP)
        raise_ = kwargs.get('raise_', False)
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
                msg = "✘ 点击异常：" + str(e)
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
        """查找元素"""
        return self._ele_(locator, index, raise_=raise_)

    def find_elements(self, locator, timeout=3, use_location=False) -> list:
        """查找元素组"""
        time.sleep(1)
        eles = self._ele_(locator, 999, timeout=timeout, raise_=False, use_location=use_location)
        # 如果有元素，内部会记录，添加一个没元素时的外部记录，没元素时强制记录定位符
        if not eles:
            eles = []
            msg = '❕ 查找元素组 [] %s' % str(locator)
            self.logger.warning(msg) if self.logger else print(msg)
        return eles

    def add_cookies(self, file_path: str):
        """通过文件读取cookies"""
        with open(file_path, "r") as f:
            ck = f.read()
        cookie_list = eval(ck)
        if isinstance(cookie_list, list):
            for cookie in cookie_list:
                self.driver.add_cookie(cookie)
        else:
            raise TypeError("cookies类型错误，它是个列表套字典")

    def save_cookies_to_file(self, file_path: str):
        """把cookies保存到文件"""
        ck = self.driver.get_cookies()
        with open(file_path, 'w') as f:
            f.write(str(ck))

    def set_attribute(self, locator, attribute: str, value, index=0):
        """设置属性"""
        elem = self._ele_(locator, index=index)
        self.driver.execute_script("arguments[0].setAttribute(arguments[1],arguments[2])", elem, attribute, value)

    def switch_to_alert(self):
        """切换到浏览器弹窗"""
        try:
            return self.driver.switch_to.alert
        except NoAlertPresentException:
            return False

    def dismiss_alert(self):
        """浏览器弹窗取消"""
        self.driver.switch_to.alert.dismiss()

    def stretch(self, size=0.8):
        """
        页面放大/缩小
        :param size: 放大/缩小百分比
        """
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.execute_script(js)

    def release(self):
        """释放动作"""
        ActionChains(self.driver).release().perform()

    def text(self, locator, index=0, timeout=8):
        """元素文本"""
        elem = self._ele_(locator, index, timeout=timeout, count=0)  # 在批量获取时去掉闪烁不然太浪费时间。
        try:
            text = elem.text
        except (StaleElementReferenceException, WebDriverException):
            text = ''
        return text

    def clear(self, locator, index=0, raise_=True):
        """
        清空输入框，清空2次，兼容复杂情况
        """
        elem = self._ele_(locator, index, raise_=raise_)
        self.click(elem)
        elem.clear()
        time.sleep(0.05)
        elem.clear()

        # 全选删除（一不小心就全选整个页面了）
        if 'input' in locator:
            self.click(elem)
            self.select_all(elem)
            self.backspace(elem)

    def get_attribute(self, name, locator, index=0, **kwargs):
        """获取元素属性"""
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        raise_ = kwargs.get('raise_', False)
        elem = self._ele_(locator, index, timeout=3, raise_=raise_, pre_sleep=pre_sleep)
        if elem:
            return elem.get_attribute(name)

    def get_property(self, name, locator, index=0):
        """获取元素对应的浏览器记录属性"""
        elem = self._ele_(locator, index=index, pre_sleep=0.5)
        return elem.get_property(name)

    def get_css_property(self, name, locator, index=0):
        """获取样式"""
        elem = self._ele_(locator, index, timeout=3, pre_sleep=0.5)
        return elem.value_of_css_property(name)

    def is_selected(self, locator, index=0):
        """可以用来检查 checkbox or radio button 是否被选中"""
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

        # 也要判断上一个
        attr_value2 = self.get_attribute(name='class', locator=self._locator_(locator)[0] + '/ancestor::*[1]',
                                         raise_=False)
        if attr_value2:
            flag3 = all(map(lambda x: x not in attr_value2, dis_flag))
        return all([flag1, flag2, flag3])

    def is_clickable(self, locator, index=0, timeout=3, attr='class'):
        """是否可点击，叫法不一样为了兼容"""
        return self.is_enable(locator, index=index, timeout=timeout, attr=attr)

    def get(self, uri):
        """请求地址"""
        self.driver.get(uri)
        msg = f'✔ 请求地址 {uri}'
        self.logger.info(msg) if self.logger else print(msg)

    def title(self):
        """浏览器标题"""
        return self.driver.title

    def save_screenshot(self, path, filename=None):
        """截图"""
        if not filename:
            filename = datetime.now().strftime('%Y%m%d%H%M%S%f') + '.png'
        file_path = os.path.join(path, filename)
        self.driver.save_screenshot(file_path)

    def current_url(self):
        """当前地址"""
        return self.driver.current_url

    @property
    def page_source(self):
        """页面html"""
        return self.driver.page_source

    def quit(self):
        """退出"""
        try:
            self.driver.quit()
        except Exception:
            ...  # 'WebDriver' object has no attribute 'driver'，无伤大雅
        quit_ = "✌ 退出浏览器..."
        self.driver: Wd = None  # 销毁driver
        self.logger.info(quit_) if self.logger else print(quit_)

    def close(self):
        """关闭标签页"""
        return self.driver.close()

    def maximize_window(self):
        """最大化窗口"""
        return self.driver.maximize_window()

    @property
    def switch_to(self):
        """
        切换到
        :用法:
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
        """切回默认的frame"""
        return self.driver.switch_to.default_content()

    def forward(self):
        """前进历史记录的后一步"""
        return self.driver.forward()

    def refresh(self):
        """刷新"""
        return self.driver.refresh()

    def switch_to_frame(self, frame_reference):
        """切换frame"""
        self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        """切到父frame"""
        self.driver.switch_to.parent_frame()

    def window_handles(self):
        """windows句柄"""
        return self.driver.window_handles

    def switch_to_window(self, handle):
        """切换浏览器标签页"""
        if isinstance(handle, int):
            handle = self.driver.window_handles[handle]
        self.driver.switch_to.window(handle)

    def new_tab(self, to=True):
        """新开浏览器标签页"""
        self.driver.execute_script('window.open("","_blank");')
        if to:
            self.switch_to_window(handle=-1)

    get_alert_text = property(lambda self: self.driver.switch_to.alert.text, lambda self, v: None)

    def submit(self, locator):
        """提交（没什么用）"""
        elem = self._ele_(locator)
        elem.submit()

    def tag_name(self, locator):
        """标签名（没什么用）"""
        elem = self._ele_(locator)
        return elem.tag_name

    def size(self, locator):
        """元素宽高"""
        elem = self._ele_(locator)
        return elem.size

    def move_to_element(self, locator, index=0, timeout=3, click=False, logged=True):
        """鼠标移动到元素上(点击)"""
        elem = self._ele_(locator, index=index, timeout=timeout, logged=logged)
        if click:
            ActionChains(self.driver).move_to_element(elem).click().perform()
            self.__bac_force_sleep__(locator)
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
            self.__bac_force_sleep__(locator)
        else:
            am.perform()
        ActionChains(self.driver).move_by_offset(-x, -y).perform()  # 抵消累积

    def offset_double_click(self, x=0, y=0, **kwargs):
        """鼠标双击"""
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

    def double_click(self, locator, index=0, bac_sleep=SLEEP):
        """双击"""
        for i in range(2):
            try:
                time.sleep(bac_sleep)
                elem = self._ele_(locator, index=index, timeout=5)
                ActionChains(self.driver).double_click(elem).perform()
                time.sleep(bac_sleep)
                return
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

    def drag_and_drop_by_offset(self, locator, x, y, index=0):
        """元素拖拽至坐标，横向滚动更好用"""
        elem = self._ele_(locator=locator, index=index)
        try:
            ActionChains(self.driver).drag_and_drop_by_offset(elem, xoffset=x, yoffset=y).perform()
            time.sleep(1)  # 因为对于页面来说是耗时动作
        except (ElementNotInteractableException, MoveTargetOutOfBoundsException, StaleElementReferenceException):
            try:
                x = x * 0.66 if x else x
                y = y * 0.66 if y else y
                ActionChains(self.driver).drag_and_drop_by_offset(elem, xoffset=x, yoffset=y).perform()
            except (ElementNotInteractableException, MoveTargetOutOfBoundsException, StaleElementReferenceException):
                ...  # 还滚动不了就算了，无需报错

    def location_once_scrolled_into_view(self, locator, index=0, raise_=True):
        """滚动到元素，竖向滚动更好用"""
        time.sleep(0.1)
        elem = self._ele_(locator, index=index, raise_=raise_)
        if not raise_ and not elem:
            return
        try:
            elem_view = elem.location_once_scrolled_into_view
        except WebDriverException as e:
            msg = '✘ location_once_scrolled_into_view报错' + str(e)[:10] + '...'
            self.logger.info(msg) if self.logger else print(msg)
            return
        time.sleep(0.1)
        return elem_view

    def scroll_views(self, locators, tar_locator, sep=5, **kwargs):
        """
        于元素组中滚动至目标元素出现，一般用于展开树结构
        :param locators: 要滚动的元素组
        :param tar_locator: 目标元素
        :param sep: 检测间隔（若无间隔太慢了，间隔太大可能检测不到）
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
                return True
            else:
                self.location_once_scrolled_into_view(eles[i])
        else:  # 若滚动完了还没有，则需要重新获取
            return self.scroll_views(locators, tar_locator, sep, tar_index=tar_index, n=n + 1)

    def execute_script(self, js, *args):
        """执行js"""
        return self.driver.execute_script(js, *args)

    @property
    def contains_xpath(self):
        return '//*[contains(., %s)]'

    def enter(self, locator, index=0):
        """按下 enter 键"""
        elem = self._ele_(locator, index=index)
        elem.send_keys(Keys.ENTER)

    def select_all(self, locator, index=0):
        """全选"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "a")
        else:
            elem.send_keys(Keys.CONTROL, "a")

    def cut(self, locator, index=0):
        """剪切：：ctrl+x"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "x")
        else:
            elem.send_keys(Keys.CONTROL, "x")

    def copy(self, locator, index=0):
        """复制：ctrl+c"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "c")
        else:
            elem.send_keys(Keys.CONTROL, "c")

    def paste(self, locator, index=0):
        """粘贴：ctrl+v"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "v")
        else:
            elem.send_keys(Keys.CONTROL, "v")

    def backspace(self, locator, empty: bool = True):
        """按下 回格 键"""
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.BACKSPACE)

    def delete(self, locator, empty: bool = True):
        """按下 删除 键"""
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.DELETE)

    def tab(self, locator):
        """按下 Tab 键"""
        elem = self._ele_(locator)
        elem.send_keys(Keys.TAB)

    def space(self, locator):
        """按下 空格 键"""
        elem = self._ele_(locator)
        elem.send_keys(Keys.SPACE)

    def esc(self):
        """按下 Esc 键"""
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def press(self, *keys):
        """按下 自定义 键"""
        self.switch_to.active_element.send_keys(*keys)

    # 操作的中文，方便日志打印
    __operate__ = lambda self: {
        'click': '点击 ',
        'send_keys': '输入 ',
        'normal_send': '输入 ',
        'double_click': '双击 ',
        'js_click': 'js点击 ',
        'drag_and_drop': '拖拽 ',
        'right_click': '右键点击 ',
        'find_element': '查找元素 ',
        'find_elements': '查找元素组 ',
        'get_attribute': '获取属性 ',
        'set_attribute': '设置属性 ',
        'text': '元素文本 ',
        'move_to_element': '鼠标点击 ',
        'location_once_scrolled_into_view': '滚动到 ',
        'drag_and_drop_by_offset': '拖拽 ',
        'is_selected': '是否选中 ',
    }

    @staticmethod
    def __get_locator_future__(locator):
        """获取元素自带的文本特征"""
        res = re.findall(r"text\(\)\.*.*?]", locator) or re.findall(r"holder\.*.*?]", locator)
        desc = locator

        # 有的既有文字也有following，以下能精准描述
        rtext = locator.rfind('text')
        rholder = locator.rfind('holder')
        rtext = rtext if rtext > rholder else rholder
        rfollowing = locator.rfind('following')

        if res:
            res = res[-1]  # 如果有多个text，取后一个
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
        if rfollowing > rtext:
            last_tag1 = locator.rfind('/') + 1
            last_tag2 = locator.rfind('::') + 2
            last_tag1 = last_tag1 if last_tag1 > last_tag2 else last_tag2
            last_tag3 = locator.rfind('[')
            last_tag = locator[last_tag1:last_tag3]
            if last_tag3 < last_tag1:
                last_tag = locator[last_tag1:]
            desc = desc + ' 的 ' + last_tag
        return desc


g_driver = ...


def get_driver():
    """driver实例"""
    return g_driver


def overtime(timeout):
    """检测耗时函数"""

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
        self.close_if_opened()  # 上传后不留隐患

    def __init__(self):
        self.__title__ = self.__get_title()
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
            print("❕ '打开' 窗口不存在")
            return False  # 说明点击有问题，给false的意思是让外部再触发一次。

        if not file_path:
            print("❕ 文件名为空，取消上传")
            self.__cancel(dialog)
            return True  # 文件名为空，不是点击问题，不需要外部再触发。

        self.__occur_no_exist(n=1)  # 如果一开始/上传过某些文件之后，出现‘找不到窗口’，需要关闭这个窗口，这里不管你是否出现，我都要填写，所以没必要搞个对象接收

        return self.__fill_and_open(file_path, timeout - 1)

    @staticmethod
    def __get_title():
        brs = BROWSER.lower()
        title = "打开" if brs in ["chrome", 'edge'] else "文件上传" if brs == "firefox" else False
        return title if title else print("❕ 建议用谷歌浏览器")  # 利用 print 返回的是None

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
        print('✔ ' + self.__title__ + ' (正在上传文件...)')
        open_button = self.__win32.find_window_ex(dialog, 0, 'Button', "打开(&O)")

        # 点击打开
        @overtime(1)
        def _click_open():
            self.__win32gui.SendMessage(dialog, self.__win32con.WM_COMMAND, 1, open_button)

        try:
            _click_open()
        except TimeoutError:
            print("✘ 不存在该文件，点击打开按钮超时")
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
            if not delay <= 0:
                time.sleep(delay)
            return True


class Utils:
    """
    通用工具类
    """
    cur_time = property(lambda self: datetime.now().strftime('%Y%m%d%H%M%S%f'))

    get_file_date = lambda self, file_path: datetime.fromtimestamp(os.stat(file_path).st_mtime)

    sorted_file_by_time = lambda self, dir_path, reverse=True: [
        os.path.join(dir_path, x[0]) for x in sorted([
            (file, self.get_file_date(os.path.join(dir_path, file))) for file in os.listdir(dir_path)
        ], key=lambda x: x[1], reverse=reverse)
    ]

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
    def clear_by_mtime(dir_path, days=4, count=0):
        """按创建时间清理"""
        files_date = [(file, datetime.fromtimestamp(os.stat(os.path.join(dir_path, file)).st_mtime))
                      for file in os.listdir(dir_path)]
        sorted_file = [(os.path.join(dir_path, x[0]), x[1]) for x in
                       sorted(files_date, key=lambda x: x[1], reverse=True)]
        if count:
            sorted_file = sorted_file[count:]

        for i in sorted_file:
            file, date = i
            if date < datetime.today() - timedelta(days=days) or count:
                try:
                    os.remove(file)
                except PermissionError:
                    shutil.rmtree(file)

    def clear_by_count(self, dir_path, count=10):
        """按数量清理"""
        return self.clear_by_mtime(dir_path=dir_path, count=count)

    @staticmethod
    def clear_by_type(dir_path, end='.jpg'):
        """按类型清理"""
        for i in [os.path.join(dir_path, i) for i in os.listdir(dir_path)]:
            if i.endswith(end):
                os.remove(i)

    @staticmethod
    def caption(msg):
        """自动化指令化为字幕"""
        if '没显示' in msg:
            return
        import tkinter as tk
        window = tk.Tk()
        window.geometry("520x30+780+900")
        window.title("")
        window.overrideredirect(1)
        label = tk.Label(window, text=msg)
        label.pack()
        label.config(font=("Arial", 18, "bold"), fg="red")
        window.after(500, window.destroy)
        window.mainloop()
