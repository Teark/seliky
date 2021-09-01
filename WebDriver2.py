import time
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException, WebDriverException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


class WebDriver2:
    """
    encapsulation based on webdriver in selenium
    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, browser='chrome'):
        self.driver = webdriver.Chrome() if browser == 'chrome' else webdriver.Firefox() if browser == 'firefox' else \
            webdriver.Ie() if browser == 'ie' else webdriver.Safari() if browser == 'safari' else webdriver.Chrome()

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

    def __ele(self, locator, index=0):
        """
        Find elements by its location
        :param locator: element location expression
        :param index: which one in find list
        """

        def __find_ele(locator_):
            time.sleep(0.5)
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
            try:
                elem = self.driver.find_elements(by=by, value=locator_)[index]
            except (UnboundLocalError, NoSuchElementException, IndexError):
                elem = None
                pass
            if elem:
                self.__highlight(elem)
                return elem

        if isinstance(locator, str):
            return __find_ele(locator)
        elif isinstance(locator, list):
            for i in locator:
                try:
                    ele = __find_ele(i)
                    if ele:
                        return ele
                    else:
                        continue
                except (NoSuchElementException, ValueError):
                    continue
        else:
            raise TypeError("locator must be str or list")

    def window_scroll(self, width=None, height=None):
        """
        Synchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - *args: Any applicable arguments for your JavaScript.

        :Usage:
            driver.execute_script('return document.title;')
        """
        if height is None:
            c = 1
            while True:
                ActionChains(self.driver).send_keys(Keys.UP)
                c += 1
                if c >= 100:
                    break
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
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.execute_script(js)

    def release(self):
        ActionChains(self.driver).release().perform()

    def click(self, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.click()

    def text(self, locator, index=0):
        """The text of the element."""
        elem = self.__ele(locator, index)
        return elem.text

    def clear(self, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.clear()

    def get_attribute(self, name, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.get_attribute(name)

    def is_selected(self, locator, index=0):
        """Returns whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.
        """
        elem = self.__ele(locator, index)
        return elem.is_selected()

    def is_displayed(self, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.is_displayed()

    def is_enable(self, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.is_enabled()

    def send_keys(self, value, locator, index=0):
        elem = self.__ele(locator, index)
        return elem.send_keys(value)

    def get(self, uri):
        return self.driver.get(uri)

    @property
    def title(self):
        """Returns the title of the current page.

        :Usage:
            title = driver.title
        """
        return self.driver.title

    def save_screenshot(self, filename):
        """
        Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            driver.save_screenshot('/Screenshots/foo.png')
        """
        return self.driver.get_screenshot_as_file(filename)

    @property
    def current_url(self):
        """
        Gets the URL of the current page.

        :Usage:
            driver.current_url
        """
        return self.driver.current_url

    def quit(self):
        """
        Quits the driver and closes every associated window.

        :Usage:
            driver.quit()
        """
        return self.driver.quit()

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

        :Usage:
            driver.back()
        """
        return self.driver.back()

    def forward(self):
        """
        Goes one step forward in the browser history.

        :Usage:
            driver.forward()
        """
        return self.driver.forward()

    def refresh(self):
        """
        Refreshes the current page.

        :Usage:
            driver.refresh()
        """
        return self.driver.refresh()
