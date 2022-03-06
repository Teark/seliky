import os
import platform
import subprocess
from functools import reduce
import time
from func_timeout import func_set_timeout, FunctionTimedOut
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, \
    StaleElementReferenceException, TimeoutException, InvalidSelectorException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from seliky.log import Log
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

log = Log(write_in_file=False)


class WebDriver2:
    """
    encapsulation based on webdriver in selenium
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, display: bool = True, log_: bool = False,
                 executable_path: str = 'chromedriver', options: list = '',
                 experimental_option='', loger_infile=None):
        """
        :param display: weather show dynamic, False means headless mode
        :param log_: weather show log info
        :param options: for add argument in driver, especial:
            '--headless'
            '--no-sandbox'
            '--disable-gpu'
            '--disable-dev-shm-usage'
            'window-size=1920x1080'
            'blink-settings=imagesEnabled=False'
            'user-agent="MQQBrowser/26 Mozilla/5.0 ..."'
            'user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache'
        :param experimental_option: exp:
            prefs =
            {'profile.managed_default_content_settings.images': 2,
            'profile.default_content_settings.popups': 0,
             'download.default_directory': r'd:\'}
        """
        self.display = display
        self.log_ = log_
        self.options = options
        self.experimental_option = experimental_option
        self.executable_path = executable_path
        global log
        log = loger_infile if loger_infile else log

    def open_browser(self):
        """
        open a browser, default open chrome browser
        """
        if 'chrome' in self.executable_path:
            browser_type = 'chrome'
            opt = ChromeOptions()
        else:
            browser_type = 'firefox'
            opt = FirefoxOptions()

        for i in self.options:
            opt.add_argument(i)

        if self.experimental_option:
            opt.add_experimental_option('prefs', self.experimental_option)

        if platform.system().lower() in ["windows", "macos"] and self.display:
            self.driver = webdriver.Chrome(
                executable_path=self.executable_path,
                options=opt
            ) if browser_type == 'chrome' else webdriver.Firefox(
                executable_path=self.executable_path,
                options=opt,
                service_log_path=os.devnull
            )
            self.driver.maximize_window()

        else:  # devops platform
            for i in ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']:
                opt.add_argument(i)
            self.driver = webdriver.Chrome(executable_path=self.executable_path, options=opt)
        return self.driver

    def __highlight(self, ele):
        """
        element will be red and blue in several quickly times
        :param ele: element locator
        """
        if self.display:
            try:
                for _ in range(2):
                    self.driver.execute_script('arguments[0].style.border="2px solid #FFFF00"', ele)
                    time.sleep(0.1)
                    self.driver.execute_script('arguments[0].style.border="2px solid #FF0033"', ele)
                    time.sleep(0.1)
                self.driver.execute_script('arguments[0].style.border="2px solid #FF0033"', ele)
                time.sleep(0.5)
                self.driver.execute_script('arguments[0].style.border=""', ele)
            except WebDriverException:
                pass

    @func_set_timeout(1)
    def __eles(self, key, vlaue):
        elems = self.driver.find_elements(by=key, value=vlaue)
        return elems

    def __find_ele(self, locator_, index: int = 0, timeout: int = 6, raise_=True):
        time.sleep(0.2)
        if locator_.startswith("/"):
            by = By.XPATH
            locator_ = locator_
        elif locator_.startswith("xpath"):
            by = By.XPATH
            locator_ = locator_.index('=')
        elif locator_.startswith("id"):
            by = By.ID
            locator_ = locator_[4:-1]
        elif locator_.startswith("css"):
            by = By.CLASS_NAME
            locator_ = locator_[5:-1]
        elif locator_.startswith("class"):
            by = By.CLASS_NAME
            locator_ = locator_[7:-1]
        elif locator_.startswith('class_name'):
            by = By.CLASS_NAME
            locator_ = locator_[12:-1]
        elif locator_.startswith('link'):
            by = By.LINK_TEXT
            locator_ = locator_[6:-1]
        elif locator_.startswith('link_text'):
            by = By.LINK_TEXT
            locator_ = locator_[11:-1]
        elif locator_.startswith('partial'):
            by = By.PARTIAL_LINK_TEXT
            locator_ = locator_[9:-1]
        elif locator_.startswith('partial_link_text'):
            by = By.PARTIAL_LINK_TEXT
            locator_ = locator_[19:-1]
        elif locator_.startswith('css'):
            by = By.CSS_SELECTOR
            locator_ = locator_[5:-1]
        elif locator_.startswith('css_selector'):
            by = By.CSS_SELECTOR
            locator_ = locator_[14:-1]
        elif locator_.startswith('tag'):
            by = By.TAG_NAME
            locator_ = locator_[5:-1]
        else:
            raise TypeError("you'd better write locator in xpath, such as '//div[@class='seliky']' -> %s" % locator_)
        for i in range(timeout):
            try:
                elem = self.__eles(key=by, vlaue=locator_)
                if not elem:
                    if i == timeout and raise_:
                        raise ValueError('no such ele %s' % locator_)
                    self.switch_to().default_content()
                    time.sleep(0.8)
                    continue
                if index != 999:
                    try:
                        elem = elem[index]  # The first one is selected by default
                    except IndexError:
                        log.warn('IndexError: index out of range, choose the first')
                        elem = elem[0]
                self.__highlight(elem)
                return elem
            except (FunctionTimedOut, InvalidSelectorException, SyntaxError) as e:
                if raise_ and i == timeout:
                    raise e
                self.switch_to().default_content()
                time.sleep(0.6)
                continue

    def __ele(self, locator, index=0, timeout=6, raise_=True, log_=None, log_when_fail=True):
        """
        Find elements by its location
        """
        log_ = self.log_ if log_ is None else log_
        if isinstance(locator, str):
            ele = self.__find_ele(locator, index, timeout, raise_)
            if ele:
                if log_:
                    log.info("☺ ✔ %s" % locator)
                return ele
            else:
                if raise_:
                    raise ValueError("Not find element %s, please check locator expression" % locator)
                else:
                    if log_when_fail:
                        log.error("☹ ✘ %s" % locator)
        elif isinstance(locator, list or tuple):
            for i in locator:
                ele = self.__find_ele(i, index, timeout)
                if ele:
                    log.warn("☹ - the valid selector is %s, you can remove others in it's list" % i)
                    return ele
                else:
                    if locator.index(i) == len(locator) - 1:
                        log.error("☹ ✘ no right ele in the locator list %s" % locator)
                    else:
                        continue
        else:
            raise TypeError("locator must be str or iterable type %s" % locator)

    def click(self, locator, index: int = 0, timeout: int = 6,
              pre_sleep=0.1, bac_sleep=0.1, raise_: bool = True):
        """
        click element
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
                        log.error('click failed %s, reason belows' % locator)
                        raise e
            elif i == 1 and raise_:
                raise ValueError('no such ele %s' % locator)

    def send_keys(self, locator, value,
                  index: int = 0, timeout: int = 6, clear: bool = True,
                  pre_sleep=0, bac_sleep=0, raise_=True, enter=False):
        """
        Send value to input box

        Usage:
            driver.send_keys("hello", "id=kw")
        """
        time.sleep(pre_sleep)
        elem = self.__ele(locator, index, timeout, raise_=raise_)
        if elem:
            if clear:
                elem.clear()
            elem.send_keys(value)
            if enter:
                elem.send_keys(Keys.ENTER)
            time.sleep(bac_sleep)
        else:
            if raise_:
                raise ValueError("ValueError: no such elem - %s" % locator)
            else:
                log.error('no such elem - %s' % locator)

    def upload(self, locator: str, file_path: str, timeout=6):
        """
        upload in traditional way: send files to input label
        """
        elem = self.__ele(locator, 0, timeout)
        if elem:
            elem.send_keys(file_path)
            time.sleep(timeout)
        else:
            raise ValueError("ValueError: no such elem - %s" % locator)

    @staticmethod
    def upload_with_autoit(file_path: str, uploader, timeout=6):
        """
        After wake-up system upload pop-up window，Call this method to upload files
        this is au3 script by autoit:
        """
        params = [uploader, file_path]
        interpret_code = reduce(lambda a, b: '{0} {1}'.format(str(a), '"{}"'.format(str(b))), params)
        time.sleep(0.5)
        sub_pop = 0
        try:
            sub_pop = subprocess.Popen(interpret_code)
        except FileNotFoundError:
            log.error("上传器路径没找到")
        try:
            sub_pop.wait(timeout)
        except subprocess.TimeoutExpired:
            if sub_pop:
                sub_pop.kill()
        finally:
            time.sleep(timeout)

    def is_displayed(self, locator: str, timeout: int = 6):
        """
        weather the element is displayed in html dom
        """
        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.presence_of_element_located((By.XPATH, locator)))
        except TimeoutException:
            ele = False
        return ele

    def is_visible(self, locator: str, timeout: int = 6):
        """
        weather the element is visible, css not hidden, return a bool
        """
        try:
            ele = WebDriverWait(self.driver, timeout).until(
                ec.visibility_of_element_located((By.XPATH, locator)))
        except Exception as e:
            log.warn(e)
            ele = False
        return ele

    def click2(self, locator, index=0, timeout=6, pre_sleep=0.1, bac_sleep=0.1, raise_=False):
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
                    log.error("click fail:" + str(e))
                if not i:
                    time.sleep(1)

    def window_scroll(self, width=None, height=None):
        """
        Synchronously Executes JavaScript in the current window/frame, and there are more method to achieve
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
        add cookie from file
        """
        with open(file_path, "r") as f:
            ck = f.read()
        cookie_list = eval(ck)
        if isinstance(cookie_list, list):
            for cookie in cookie_list:
                self.driver.add_cookie(cookie)
        else:
            raise TypeError("Wrong cookies type, it must be a list")

    def save_cookies(self, file_path: str):
        """
        save cookies in file
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
        Zoom in or out of the page
        :param size: percentage of zoom in or out
        """
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.execute_script(js)

    def release(self):
        ActionChains(self.driver).release().perform()

    def text(self, locator, index=0, timeout=6):
        """
        The text of the element

        Usage:
            driver.text(id=su)
        """
        elem = self.__ele(locator, index, timeout=timeout)
        return elem.text

    def clear(self, locator, index=0):
        """
        clear a input box
        """
        elem = self.__ele(locator, index)
        return elem.clear()

    def get_attribute(self, name, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.get_attribute(name)

    def is_selected(self, locator, index=0):
        """
        whether the element is selected, return a bool, Can be used to check if a checkbox or radio button is selected.
        To reader:
        This kind of judgment will be added to judge whether or not. Why not add others?
        It will report an error, but whether to return yes or no instead of returning an error
        """
        elem = self.__ele(locator, index)
        if elem:
            return elem.is_selected()
        else:
            return False

    def is_enable(self, locator, index=0, timeout=6):
        """
        weather clickable
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
        Request a page
        :param uri: url of the page

        Usage:
            driver.get("https://www.baidu.com")
        """
        return self.driver.get(uri)

    def title(self):
        """
        Returns the title of the current page.
        """
        return self.driver.title

    def save_screenshot(self, path=None, filename=None):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.
        """
        if path is None:
            path = os.getcwd()
        if filename is None:
            filename = str(time.time()).split(".")[0] + ".png"
        file_path = os.path.join(path, filename)
        self.driver.save_screenshot(file_path)

    def current_url(self):
        """
        Gets the URL of the current page.
        """
        return self.driver.current_url

    def quit(self):
        """
        Quits the driver and closes every associated window.
        """
        if self.log_:
            log.info("✌ ending...")
        self.driver.quit()

    def close(self):
        return self.driver.close()

    def maximize_window(self):
        """
        Maximizes the current window that webdriver is using
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
        Goes one step backward in the browser history.
        """
        return self.driver.back()

    def default_content(self):
        return self.driver.switch_to.default_content()

    def forward(self):
        """
        Goes one step forward in the browser history.
        """
        return self.driver.forward()

    def refresh(self):
        """
        Refreshes the current page.
        """
        return self.driver.refresh()

    def switch_to_frame(self, frame_reference):
        """
        Switches focus to the specified frame, by index, name, or webelement.
        """
        self.driver.switch_to.frame(frame_reference)

    def switch_to_parent_frame(self):
        """
        Switches focus to the parent context. If the current context is the top
        level browsing context, the context remains unchanged.
        """
        self.driver.switch_to.parent_frame()

    def window_handles(self):
        """
        Returns the handles of all windows within the current session.
        """
        return self.driver.window_handles

    def new_window_handle(self):
        """
        open a new tag
        """
        return self.window_handles()[-1]

    def switch_to_window(self, handle):
        """
        Switches focus to the specified window.
        """
        if handle == 0:
            handle = self.driver.window_handles[0]
        elif handle == 1:
            handle = self.driver.window_handles[1]
        self.driver.switch_to.window(handle)

    def dismiss_alert(self):
        """
        Dismisses the alert available.
        """
        self.driver.switch_to.alert.dismiss()

    @property
    def get_alert_text(self):
        """
        switch to alert then get it's text
        """
        return self.driver.switch_to.alert.text

    def submit(self, locator):
        """
        Submits a form
        """
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
        for i in range(6):
            if elem is not None:
                try:
                    elem
                except StaleElementReferenceException:
                    self.driver.refresh()
                else:
                    break
            else:
                time.sleep(1)
        else:
            raise TimeoutError("element is not attached to the page document.")

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
        Execute JavaScript scripts.
        """
        if js is None:
            raise ValueError("Please input js script")
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
