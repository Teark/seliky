import os
import platform
import subprocess
from functools import reduce
import time
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, \
    StaleElementReferenceException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webdriver import WebDriver as Wd
from webdriver_manager.chrome import ChromeDriverManager as Manager
from selenium.webdriver.chrome.service import Service


class WebDriver:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(
            self,
            executable_path: str = r"D:\s\python38\chromedriver.exe",
            display: bool = True,
            logger=None,  # loguru object
            options: list = '',
            experimental_option: dict = '',
            highlight: float = 0.06,  # the same as mro
    ):
        """
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
        :param experimental_option: 特殊设置项，例如:
            prefs =
            {'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.popups': 0,
             'download.default_directory': r'd:\'}
        """
        if highlight > 1:
            raise AttributeError('闪烁间隔必须小于1秒')
        self.highlight = highlight
        self.display = display
        self.options = options
        self.experimental_option = experimental_option
        self.executable_path = executable_path
        self.logger = logger
        self.driver: Wd

    def open_browser(self, re_open=False):
        """
        打开浏览器，默认打开谷歌
        """
        executable_path = self.executable_path.lower()
        if 'chrome' in executable_path:
            browser_type = 'chrome'
            opt = ChromeOptions()
            for i in self.options:
                opt.add_argument(i)

            if self.experimental_option:
                opt.add_experimental_option('prefs', self.experimental_option)

        else:
            browser_type = 'firefox'
            opt = FirefoxOptions()
            for k, v in self.experimental_option.items():
                opt.set_preference(k, v)

        try:
            if platform.system().lower() in ["windows", "macos"] and self.display:
                if browser_type == 'chrome':
                    self.driver = webdriver.Chrome(
                        executable_path=self.executable_path,
                        options=opt
                    )
                else:
                    self.driver = webdriver.Firefox(
                        executable_path=self.executable_path,
                        options=opt,
                        service_log_path=os.devnull
                    )
                self.driver.maximize_window()

            else:  # 无界面方式/流水线
                for i in ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']:
                    opt.add_argument(i)
                if browser_type == 'chrome':
                    self.driver = webdriver.Chrome(executable_path=self.executable_path, options=opt)
                else:
                    self.driver = webdriver.Firefox(executable_path=self.executable_path, options=opt)
            time.sleep(1)  # 有user-dir的时候需要等待一下
        except WebDriverException as e:
            print(e)
            if re_open:  # 说明第二次故障
                raise EnvironmentError
            new_path = Manager().install()
            import shutil
            try:
                shutil.copy(new_path, self.executable_path)
            except Exception:  # 可能报错：permission not allowed
                ...
            if browser_type == 'chrome':
                self.driver = webdriver.Chrome(service=Service(new_path))  # 如此甚好，记得selenium>4.0.0
            else:
                raise ConnectionError('firefox的镜像需要手动下载，github访问不了...')
            return self.open_browser(re_open=True)
        return self.driver

    def __highlight(self, ele):
        """
        每一步的高亮
        :param ele: ui element
        """
        if not self.highlight:
            return
        js = 'arguments[0].style.border="2px solid '
        if self.display:
            try:
                for _ in range(2):
                    self.driver.execute_script(js + '#FFFF00"', ele)
                    time.sleep(self.highlight)
                    self.driver.execute_script(js + '#FF0033"', ele)
                    time.sleep(self.highlight)
                self.driver.execute_script(js + '#FF0033"', ele)
                time.sleep(self.highlight * 5)
                self.driver.execute_script('arguments[0].style.border=""', ele)
            except WebDriverException:
                pass

    def __find_ele(self, locator_, index: int = 0, timeout: int = 10, raise_=True, is_light=True):
        time.sleep(0.1)
        if locator_.startswith("/"):
            by = By.XPATH
            locator_ = locator_
        else:
            raise TypeError("请写xpath表达式，例如 '//div[@class='seliky']' -> %s" % locator_)
        try:
            for i in range(int(timeout / 2)):
                if self.is_displayed(by=by, locator=locator_, timeout=2):
                    elems = self.driver.find_elements(by=by, value=locator_)
                    if index == 999:  # elem list
                        elem = elems
                    else:
                        elem = elems[index]
                        if is_light:
                            self.__highlight(elem)
                    return elem
                else:
                    # self.switch_to().default_content()
                    continue
                # except (FunctionTimedOut, InvalidSelectorException, SyntaxError) as e:
        except Exception as e:
            if raise_:
                raise e

    def __ele(self, locator, index=0, timeout=10, raise_=True, log_when_fail=True, is_light=True):
        """
        查找元素
        """
        if isinstance(locator, str):
            ele = self.__find_ele(locator, index, timeout, raise_, is_light=is_light)
            if ele:
                msg = "☺ ✔ %s" % locator
                self.logger.info(msg) if self.logger else print(msg)
                return ele
            else:
                if raise_:
                    raise ValueError("没找到元素 %s, 请检查表达式" % locator)
                else:
                    if log_when_fail:
                        msg = "☹ ✘ %s" % locator
                        self.logger.error(msg) if self.logger else print(msg)
        elif isinstance(locator, list or tuple):
            timeout = int(timeout / len(locator)) + 2
            for i in locator:
                ele = self.__find_ele(i, index, timeout)
                if ele:
                    msg = "☹ - 有效元素为 %s, 你可以把元素列表中的其他元素删了" % i
                    self.logger.warnning(msg) if self.logger else print(msg)
                    return ele
                elif locator.index(i) == len(locator) - 1:
                    msg = "☹ ✘ 元素列表中没有有效元素 %s" % locator
                    self.logger.error(msg) if self.logger else print(msg)
        else:
            raise TypeError

    def click(self, locator, index: int = 0, timeout=10,
              pre_sleep=0.1, bac_sleep=0.1, raise_: bool = True):
        """
        点击元素
        """
        time.sleep(pre_sleep)
        for i in range(2):
            elem = self.__ele(locator, index, timeout, raise_)
            if elem:
                try:
                    time.sleep(0.1)
                    elem.click()
                    if not i:
                        time.sleep(bac_sleep)
                    return elem
                except Exception as e:
                    if raise_ and i == 1:
                        msg = '点击失败 %s, 因为：' % locator
                        self.logger.error(msg) if self.logger else print(msg)
                        raise e
            elif i == 1 and raise_:
                raise ValueError('没有此元素：%s' % locator)

    def send_keys(self, locator, value,
                  index: int = 0, timeout: int = 10, clear: bool = True,
                  pre_sleep=0, bac_sleep=0, raise_=True, enter=False):
        """
        输入框输入值，上传请用upload方法
        """
        time.sleep(pre_sleep)
        elem = self.__ele(locator, index, timeout, raise_=raise_)
        if elem:
            if clear:
                try:
                    elem.clear()  # 上传时这里引发过错误
                except Exception:
                    ...
            elem.send_keys(value)
            if enter:
                elem.send_keys(Keys.ENTER)
            time.sleep(bac_sleep)
        else:
            msg = '没有此元素：%s' % locator
            if raise_:
                raise ValueError(msg)
            else:
                self.logger.error(msg) if self.logger else print(msg)

    def upload(self, locator: str, file_path: str, index=0, timeout=10):
        """
        上传，内部还是send_keys
        """
        elem = self.__ele(locator, index, timeout)
        if elem:
            elem.send_keys(file_path)
            time.sleep(timeout)
        else:
            raise ValueError('没有此元素：%s' % locator)

    def upload_with_autoit(self, file_path: str, uploader, timeout=10):
        """
        调用上传器，上传器exe 内部是通过 autoit制作的au3脚本
        """
        params = [uploader, file_path]
        interpret_code = reduce(lambda a, b: '{0} {1}'.format(str(a), '"{}"'.format(str(b))), params)
        time.sleep(0.5)
        sub_pop = 0
        try:
            sub_pop = subprocess.Popen(interpret_code)
        except FileNotFoundError:
            msg = "上传器路径没找到"
            self.logger.error(msg) if self.logger else print(msg)
        try:
            sub_pop.wait(timeout)
        except subprocess.TimeoutExpired:
            if sub_pop:
                sub_pop.kill()
        finally:
            time.sleep(timeout)

    def is_displayed(self, locator: str, by='xpath', timeout: int = 10):
        """
        是否展示在 html dom 里
        """
        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located((by, locator)))
        except TimeoutException:
            ele = False
        return ele

    def is_visible(self, locator: str, by='xpath', timeout=10):
        """
        是否可见，css非隐藏
        """
        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.visibility_of_element_located((by, locator)))
        except TimeoutException:
            ele = False
        return ele

    def click2(self, locator, index=0, timeout=10, pre_sleep=0.1, bac_sleep=0.1, raise_=False):
        time.sleep(pre_sleep)
        for i in range(2):
            try:
                elem = self.__ele(locator, index=index, timeout=timeout)
                self.driver.execute_script("arguments[0].click();", elem)
                time.sleep(bac_sleep)
                return elem
            except Exception as e:
                if raise_:
                    raise e
                else:
                    msg = "点击异常：" + str(e)
                    self.logger.error(msg) if self.logger else print(msg)
                if not i:
                    time.sleep(1)

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

    def find_element(self, locator, index=0):
        return self.__ele(locator, index)

    def find_elements(self, locator):
        return self.__ele(locator, 999)

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
            raise TypeError("cookies类型错误，它是个列表")

    def save_cookies(self, file_path: str):
        """
        把cookies保存到文件
        """
        ck = self.driver.get_cookies()
        with open(file_path, 'w') as f:
            f.write(str(ck))

    def set_attribute(self, locator: str, attribute: str, value):
        elem = self.__ele(locator)
        self.driver.execute_script("arguments[0].setAttribute(arguments[1],arguments[2])", elem, attribute, value)

    def alert_is_display(self):
        try:
            return self.driver.switch_to.alert
        except NoAlertPresentException:
            return False

    def move_by_offset(self, x, y, click=False):
        if click is True:
            ActionChains(self.driver).move_by_offset(x, y).click().perform()
        else:
            ActionChains(self.driver).move_by_offset(x, y).perform()

    def stretch(self, size=0.8):
        """
        页面放大/缩小
        :param size: 放大/缩小百分比
        """
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.execute_script(js)

    def release(self):
        ActionChains(self.driver).release().perform()

    def text(self, locator, index=0, timeout=6):
        """
        元素的文本
        """
        elem = self.__ele(locator, index, timeout=timeout, is_light=False)  # 爬虫中获取text，去掉高亮不然太浪费时间。
        return elem.text

    def clear(self, locator, index=0):
        """
        清空输入框
        """
        elem = self.__ele(locator, index)
        return elem.clear()

    def get_attribute(self, name, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.get_attribute(name)

    def is_selected(self, locator, index=0):
        """
        可以用来检查 checkbox or radio button 是否被选中
        To reader:
        This kind of judgment will be added to judge whether or not. Why not add others?
        It will report an error, but whether to return yes or no instead of returning an error
        """
        elem = self.__ele(locator, index)
        if elem:
            return elem.is_selected()
        else:
            return False

    def is_enable(self, locator, index=0, timeout=10):
        """
        是否可点击
        """
        elem = self.__ele(locator, index)
        for i in range(timeout):
            flag = elem.is_enabled()
            if not flag:
                time.sleep(0.9)
            else:
                return flag

    def get(self, uri):
        """
        请求url
        """
        return self.driver.get(uri)

    def title(self):
        """
        当前tab页标题
        """
        return self.driver.title

    def save_screenshot(self, path=None, filename=None):
        """
        截图
        """
        if path is None:
            path = os.getcwd()
        if filename is None:
            filename = str(time.time()).split(".")[0] + ".png"
        file_path = os.path.join(path, filename)
        self.driver.save_screenshot(file_path)

    def current_url(self):
        """
        当前地址
        """
        return self.driver.current_url

    def quit(self):
        """
        退出
        """
        quit_ = "✌ ending..."
        self.logger.info(quit_) if self.logger else print(quit_)
        self.driver.quit()

    def close(self):
        return self.driver.close()

    def maximize_window(self):
        """
        最大化
        """
        return self.driver.maximize_window()

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
        """
        返回历史记录的前一步
        """
        return self.driver.back()

    def default_content(self):
        return self.driver.switch_to.default_content()

    def forward(self):
        """
        前进历史记录的后一步
        """
        return self.driver.forward()

    def refresh(self):
        """
        刷新
        """
        return self.driver.refresh()

    def switch_to_frame(self, frame_reference):
        """
        切换到frame
        """
        self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        self.driver.switch_to.parent_frame()

    def window_handles(self):
        return self.driver.window_handles

    def new_window_handle(self):
        return self.window_handles()[-1]

    def switch_to_window(self, handle):
        if handle == 0:
            handle = self.driver.window_handles[0]
        elif handle == 1:
            handle = self.driver.window_handles[1]
        self.driver.switch_to.window(handle)

    def dismiss_alert(self):
        self.driver.switch_to.alert.dismiss()

    @property
    def get_alert_text(self):
        return self.driver.switch_to.alert.text

    def submit(self, locator):
        elem = self.__ele(locator)
        elem.submit()

    def tag_name(self, locator):
        elem = self.__ele(locator)
        return elem.tag_name

    def size(self, locator):
        elem = self.__ele(locator)
        return elem.size

    def get_property(self, locator, name):
        elem = self.__ele(locator)
        return elem.get_property(name)

    def move_to_element(self, locator, click=False):
        elem = self.__ele(locator)
        if click:
            ActionChains(self.driver).move_to_element(elem).perform()
        else:
            ActionChains(self.driver).move_to_element(elem)

    def hover(self, locator):
        return self.move_to_element(locator, click=False)

    def click_and_hold(self, locator):
        elem = self.__ele(locator)
        ActionChains(self.driver).click_and_hold(elem).perform()

    def double_click(self, locator):
        elem = self.__ele(locator)
        ActionChains(self.driver).double_click(elem).perform()

    def context_click(self, locator):
        elem = self.__ele(locator)
        ActionChains(self.driver).context_click(elem).perform()

    def drag_and_drop(self, source, target):
        elem1 = self.__ele(source)
        elem2 = self.__ele(target)
        ActionChains(self.driver).drag_and_drop(elem1, elem2).perform()

    def drag_and_drop_by_offset(self, locator, x, y):
        elem = self.__ele(locator)
        ActionChains(self.driver).drag_and_drop_by_offset(elem, xoffset=x, yoffset=y).perform()

    def refresh_element(self, locator):
        elem = self.__ele(locator)
        for i in range(3):
            if elem:
                try:
                    elem
                except StaleElementReferenceException:
                    self.driver.refresh()
                else:
                    break
            else:
                time.sleep(1)
        else:
            raise TimeoutError("元素还没抵达页面")

    @staticmethod
    def select_by_value(elem, value):
        Select(elem).select_by_value(value)

    @staticmethod
    def select_by_index(elem, index):
        Select(elem).select_by_index(index)

    @staticmethod
    def select_by_visible_text(elem, text):
        Select(elem).select_by_visible_text(text)

    def location_once_scrolled_into_view(self, locator):
        elem = self.__ele(locator)
        return elem.location_once_scrolled_into_view

    def execute_script(self, js=None, *args):
        """
        执行js
        """
        if js is None:
            raise ValueError("请输入js")
        return self.driver.execute_script(js, *args)

    def enter(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.ENTER)

    def select_all(self, locator):
        elem = self.__ele(locator)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "a")
        else:
            elem.send_keys(Keys.CONTROL, "a")

    def cut(self, locator):
        elem = self.__ele(locator)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "x")
        else:
            elem.send_keys(Keys.CONTROL, "x")

    def copy(self, locator):
        elem = self.__ele(locator)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "c")
        else:
            elem.send_keys(Keys.CONTROL, "c")

    def paste(self, locator):
        elem = self.__ele(locator)
        if platform.system().lower() == "darwin":
            elem.send_keys(Keys.COMMAND, "v")
        else:
            elem.send_keys(Keys.CONTROL, "v")

    def backspace(self, locator, empty: bool = True):
        elem = self.__ele(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.BACKSPACE)

    def delete(self, locator, empty: bool = True):
        elem = self.__ele(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.send_keys(Keys.COMMAND, "a")
            else:
                elem.send_keys(Keys.CONTROL, "a")
        elem.send_keys(Keys.DELETE)

    def tab(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.TAB)

    def space(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.SPACE)

    def esc(self):
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
