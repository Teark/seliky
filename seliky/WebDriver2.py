import os
import platform
import time

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, NoSuchElementException, \
    StaleElementReferenceException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from seliky import log


class WebDriver2:
    """
    encapsulation based on webdriver in selenium
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def open_browser(self, browser='chrome', display: bool = True):
        if platform.system().lower() in ["windows", "macos"] and display:
            self.driver = webdriver.Chrome() if browser == 'chrome' else webdriver.Firefox() if browser == 'firefox' else \
                webdriver.Ie() if browser == 'ie' else webdriver.Safari() if browser == 'safari' else webdriver.Chrome()
            self.driver.maximize_window()
        else:
            options = webdriver.ChromeOptions()
            for i in ['--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']:
                options.add_argument(i)
            self.driver = webdriver.Chrome(options=options)

    def __highlight(self, ele):
        """
        element will be red and blue in several quickly times
        :param ele: element locator
        """
        try:
            for _ in range(2):
                self.driver.execute_script('arguments[0].style.border="2px solid #FF0000"', ele)
                time.sleep(0.1)
                self.driver.execute_script('arguments[0].style.border="2px solid #00FF00"', ele)
                time.sleep(0.1)
            self.driver.execute_script('arguments[0].style.border="2px solid #00FF00"', ele)
            time.sleep(0.5)
            self.driver.execute_script('arguments[0].style.border=""', ele)
        except WebDriverException:
            pass

    def __find_ele(self, locator_, index=0, timeout=3):
        time.sleep(0.1)
        if locator_.startswith("//"):
            by = By.XPATH
        elif locator_.startswith("xpath"):
            by = By.XPATH
            locator_ = locator_[6:]
        elif locator_.startswith("id"):
            by = By.ID
            locator_ = locator_[3:]
        elif locator_.startswith("css"):
            by = By.CLASS_NAME
            locator_ = locator_[4:]
        elif locator_.startswith("class"):
            by = By.CLASS_NAME
            locator_ = locator_[6:]
        else:
            raise TypeError("you'd better write locator in xpath")
        n = 0
        while True:
            n += 1
            try:
                elem = WebDriverWait(self.driver, timeout).until(lambda x: x.find_elements(by, locator_))[index]
                if elem:
                    self.__highlight(elem)
                    return elem
            except (TimeoutException, NoSuchElementException, IndexError, StaleElementReferenceException):
                if n < 2:
                    continue
                else:
                    break

    def __ele(self, locator, index=0):
        """
        Find elements by its location
        :param locator: element location expression
        :param index: which one in find list
        """
        if isinstance(locator, str):
            ele = self.__find_ele(locator, index)
            if ele:
                return ele
            else:
                log.error("☹ ✘ %s" % locator)
                raise ValueError("Not find element %s, please check locator expression" % locator)
        elif isinstance(locator, list):
            for i in locator:
                ele = self.__find_ele(i, index, timeout=3)
                if ele:
                    log.info("☺ ✔ %s" % i)
                    return ele
                else:
                    log.warn("☹ - %s" % i)
                    if locator.index(i) == len(locator) - 1:
                        raise ValueError("no such ele")
                    else:
                        continue
        else:
            raise TypeError("locator must be str or list")

    def click(self, locator, index=0):
        """
        click a element by it's locator
        :param locator: Positioning expression
        :param index: If there are more than one, use the first one

        Usage:
            driver.click(id=su)
        """
        elem = self.__ele(locator, index)
        if elem and isinstance(locator, str):
            log.info("☺ ✔ %s" % locator)
        try:
            return elem.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", elem)

    def window_scroll(self, width=None, height=None):
        """
        Synchronously Executes JavaScript in the current window/frame.
        """
        if height is None:
            self.execute_script("var q=document.body.scrollTop=0")
            # self.execute_script("var q=document.documentElement.scrollTop=0")
            # time.sleep(1)
            # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            # c = 1
            # while True:
            #     time.sleep(0.02)
            #     ActionChains(self.driver).send_keys(Keys.UP)
            #     c += 1
            #     if c >= 100:
            #         break
            # self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
            # self.execute_script("var q=document.documentElement.scrollTop=0")
            # self.execute_script("var q=document.body.scrollTop=0")
            # self.execute_script("var q=document.getElementsByClassName('main')[0].scrollTop=0")
        else:
            width = "0" if not width else width
            height = "0" if not height else height
            js = "window.scrollTo({w},{h});".format(w=str(width), h=height)
            self.driver.execute_script(js)

    def login_with_cookie(self, before_url, after_url, cookie_path):
        self.driver.get(before_url)
        with open(cookie_path, "r") as f:
            ck = f.read()
        time.sleep(1)
        self.add_cookies(eval(ck))
        time.sleep(2)
        self.driver.get(after_url)

    def add_cookies(self, cookie_list):
        if isinstance(cookie_list, list):
            for cookie in cookie_list:
                self.driver.add_cookie(cookie)
        else:
            raise TypeError("Wrong cookie type.")

    def alert_is_display(self):
        try:
            self.driver.switch_to.alert
        except NoAlertPresentException:
            return False
        else:
            return True

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

    def text(self, locator, index=0):
        """
        The text of the element
        :param locator: Positioning expression
        :param index: If there are more than one, use the first one

        Usage:
            driver.text(id=su)
        """
        elem = self.__ele(locator, index)
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
        whether the element is selected, return a bool
        Can be used to check if a checkbox or radio button is selected.
        """
        elem = self.__ele(locator, index)
        return elem.is_selected()

    def is_displayed(self, locator, index=0):
        """
        weather the element is displayed, return a bool
        """
        elem = self.__ele(locator, index)
        if elem:
            return elem.is_displayed()
        else:
            return False

    def is_enable(self, locator, index=0):
        elem = self.__ele(locator, index)
        if elem:
            return elem.is_enabled()
        else:
            return False

    def send_keys(self, locator, value, index=0, clear: bool = False):
        """
        Send value to input box
        :param locator: Positioning expression
        :param value: the value to put
        :param index: which one, default the first
        :param clear: weather clear

        Usage:
            driver.send_keys("hello", "id=kw")
        """
        elem = self.__ele(locator, index)
        if clear:
            self.clear(locator)
        if elem:
            return elem.send_keys(value)
        else:
            raise ValueError("no such elem")

    def get(self, uri):
        """
        Request a page, which is the first thing you have to do
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
        log.info("✌ \nending at %s ..." % log.now_time)
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

    def move_to_element(self, locator):
        elem = self.__ele(locator)
        ActionChains(self.driver).move_to_element(elem).perform()

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

    def select_by_value(self, locator, value):
        select_elem = self.__ele(locator)
        Select(select_elem).select_by_value(value)

    def select_by_index(self, locator, index):
        select_elem = self.__ele(locator)
        Select(select_elem).select_by_index(index)

    def select_by_visible_text(self, locator, text):
        select_elem = self.__ele(locator)
        Select(select_elem).select_by_visible_text(text)

    def location_once_scrolled_into_view(self, locator):
        elem = self.__ele(locator)
        return elem.location_once_scrolled_into_view()

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

    def backspace(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.BACKSPACE)

    def delete(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.DELETE)

    def tab(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.TAB)

    def space(self, locator):
        elem = self.__ele(locator)
        elem.send_keys(Keys.SPACE)

    def execute_script(self, js=None, *args):
        """
        Execute JavaScript scripts.
        """
        if js is None:
            raise ValueError("Please input js script")
        return self.driver.execute_script(js, *args)

    """
    ==================为了让rf无缝替换====================
    """

    def click_button(self, locator, index=0):
        return self.click(locator, index)

    def click_element(self, locator, index=0):
        return self.click(locator, index)

    def click_image(self, locator, index=0):
        return self.click(locator, index)

    def click_link(self, locator, index=0):
        return self.click(locator, index)

    def close_browser(self):
        return self.quit()

    def close_window(self):
        return self.close()

    def get_text(self, locator):
        elem = self.__ele(locator)
        return elem.text

    def get_title(self):
        return self.title()

    def go_to(self, uri):
        return self.get(uri)

    def input_password(self, locator: str, value: str, clear: bool = True):
        return self.send_keys(value, locator, clear)

    def input_text(self, locator: str, value: str, clear: bool = True):
        return self.send_keys(value, locator, clear)
