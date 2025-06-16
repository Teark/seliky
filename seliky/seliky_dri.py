from datetime import datetime
import platform
from DrissionPage import ChromiumPage
from DrissionPage import ChromiumOptions
from DrissionPage.items import ChromiumElement
from DrissionPage._functions.keys import Keys
from DrissionPage._units.actions import Actions
import inspect
import re
import time
import os
from seliky.seliky import upload

BROWSER = 'chrome'


class WebDriver:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'  # 兼容 robot framework
    SLEEP = 0  # 前后置等待初始时间（0.1~0.5）
    FLASH_CT = 3  # 为1很好，亮一次即可；除非演示或需要高亮可置为2

    def __init__(
            self,
            display: bool = True,
            logger=None,
            log_locator: bool = False,
            options: list = '',
            experimental_option: dict = '',
            use_user_path: bool = False
    ):
        """
        :param display: 是否以界面方式显示
        :param logger: 日志对象（最好是 pytest-loguru）
        :param log_locator: 是否记录 定位表达式
        :param options: 设置项，例如:
            '--start-maximized'
            ('--window-size', '800,600')
        :param experimental_option: 特殊设置项，例如: 不加载图、取消弹窗询问、设置下载路径
        :param use_user_path: 是否使用用户路径
        """
        self.display = display
        self.options = options
        self.experimental_option = experimental_option
        self.logger = logger
        self.driver: ChromiumPage
        self.log_locator = log_locator
        self.opt = ChromiumOptions()
        self.use_user_path = use_user_path

    def open_browser(self):
        """打开谷歌内核的浏览器，默认打开谷歌"""
        global BROWSER
        for i in self.options:
            self.opt.set_argument(i)  # ('--window-size', '800,600')

        if platform.system().lower() in ["windows", "macos"] and self.display:
            if self.use_user_path:
                self.opt.use_system_user_path()
            self.driver = ChromiumPage(addr_or_opts=self.opt)
            self.ac = Actions(self.driver)
            msg = '✔ 打开浏览器'
            self.logger.info(msg) if self.logger else print(msg)
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
                    self.driver.run_js(js + '"2px solid #FF0000"', ele)
                    self.driver.run_js(js2 + '"2px solid #FF0000"', ele)
                    time.sleep(interval)
                    self.driver.run_js(js + '"2px solid #FFFF00"', ele)
                    self.driver.run_js(js2 + '"2px solid #FFFF00"', ele)
                    time.sleep(interval)
                self.driver.run_js(js + '"2px solid #FF0000"', ele)
                self.driver.run_js(js2 + '"2px solid #FF0000"', ele)
                time.sleep(interval)
                if count:
                    time.sleep(interval * 3)
                self.driver.run_js(js + '""', ele)
                self.driver.run_js(js2 + '""', ele)
            except Exception:
                ...

    def _locator_(self, locator, vague=False):
        """返回 真实locator，描述，是否为Web对象"""
        if isinstance(locator, ChromiumElement):
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
                        real_ls += '//*[text()="{0}"]'.format(i) + '|'
                    real_locator = real_ls.rstrip('|')
                else:
                    real_locator = '//*[text()="{0}"]'.format(locator)
                if vague:
                    real_locator = '//*[contains(text(),"{0}")]'.format(locator)
        else:
            raise TypeError
        real_locator = 'xpath=' + real_locator
        return real_locator, desc

    def _ele_(self, locator, index=0, timeout=8.0, **kwargs):
        """
        元素处理
        """
        if isinstance(locator, ChromiumElement):
            if index == 999:
                return [locator]
            return locator
        vague = kwargs.get('vague', False)
        logged = kwargs.get('logged', True)
        raise_ = kwargs.get('raise_', True)
        locator, desc = self._locator_(locator, vague=vague)

        # 获取描述（有反射机制莫再封，反射机制只针对当前文件对它的引用）
        try:
            func = inspect.stack()[1].function
        except IndexError:
            func = 'find_elements'
        desc = self.__operate__().get(func, '') + desc
        if self.log_locator:
            desc = desc + ' ' + locator
        pre_sleep = kwargs.get('pre_sleep', 0.01)  # 0.01也很关键
        time.sleep(pre_sleep)
        interval = [1.0 for _ in range(int(timeout))]
        ele = None
        for iv in interval:
            try:
                ele = self.driver.eles(locator=locator, timeout=iv)
            except Exception:
                continue
        if ele:
            ele = ele[index]
            self.__highlight__(ele)
            if logged:  # send_keys 无需记录因其外层有记录
                msg = "✔ %s" % (desc if desc else locator)
                self.logger.info(msg) if self.logger else print(msg)
            return ele
        else:
            if not raise_:  # 指定不抛出异常时也无需记录
                logged = False
            if logged:
                msg = "✘ %s" % desc if desc else locator
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
        except Exception as e:
            try:
                # 强制点击-不可穿透遮罩层（手动鼠标形式点击），可解决ElementClickInterceptedException; StaleElement
                self.ac_click(locator, index=index)
            except Exception as e2:
                try:
                    # 可以穿透遮罩层，可解决ElementClickInterceptedException
                    self.driver.run_js("arguments[0].click();", elem)
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
        time.sleep(sleep)
        try:
            locator, _ = self._locator_(locator)
        except TypeError:  # 有时传进来的是webelement对象
            return
        kw = locator.rfind('=') + 2
        if locator[kw:kw + 1] in ['确', '是', '搜', '创', '新']:
            time.sleep(1)  # 触发事务后等1秒

    def ac_click(self, locator, index=0):
        """鼠标点击"""
        return self.move_to_element(locator=locator, index=index, click=True)

    def send_keys(self, locator, value, index: int = 0, timeout: int = 6, clear: bool = True, enter=False, **kwargs):
        """
        输入框输入值，上传请用upload方法
        """
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        bac_sleep = kwargs.get('bac_sleep', 0.5)

        if not value and value != 0:  # 0可以有
            return
        time.sleep(pre_sleep)
        elem = self._ele_(locator, index, timeout, raise_=True, logged=False)
        if clear:
            elem.clear()
        elem.input(value)
        locator_, desc = self._locator_(locator)
        msg = '✔ 输入 ' + desc + ' ' + str(value)
        if enter:
            self.enter()
        self.logger.info(msg) if self.logger else print(msg)
        self.__bac_force_sleep__(locator, sleep=bac_sleep)

    def upload(self, locator, file_path: str, index=0, timeout=6):
        """
        通过输入值的形式上传，内部还是send_keys，处理windows弹窗上传请用uploads库
        """
        elem = self._ele_(locator, index=index, timeout=timeout * 0.8)
        elem.input(file_path)
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
        return self.is_visible(locator, timeout)

    def _desc_(self, locator, desc):
        """描述"""
        if isinstance(locator, ChromiumElement):
            locator = '$当前对象'
        return desc + locator if self.log_locator else desc

    def is_visible(self, locator, timeout=6.0):
        """
        是否可见：多元素判断+兼容原生；
        多元素情况值判断索引为0、-1、中间
        """
        return self._ele_(locator=locator, timeout=timeout, raise_=False)

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
            self.driver.run_js("arguments[0].click();", elem)
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
        滚动、下拉
        """
        if height is None:
            self.run_js("var q=document.body.scrollTop=0")
        else:
            width = "0" if not width else width
            height = "0" if not height else height
            js = "window.scrollTo({w},{h});".format(w=str(width), h=height)
            self.driver.run_js(js)

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
        """通过文件读取cookies，无"""
        ...

    def save_cookies_to_file(self, file_path: str):
        """把cookies保存到文件"""
        ck = self.driver.cookies()
        with open(file_path, 'w') as f:
            f.write(str(ck))

    def set_attribute(self, locator, attribute: str, value, index=0):
        """设置属性"""
        elem = self._ele_(locator, index=index)
        self.driver.run_js("arguments[0].setAttribute(arguments[1],arguments[2])", elem, attribute, value)

    def switch_to_alert(self):
        """切换到浏览器弹窗"""
        try:
            return self.driver.handle_alert(accept=True)
        except Exception as e:
            self.logger.warning(e) if self.logger else print(e)

    def dismiss_alert(self):
        """浏览器弹窗取消"""
        self.driver.handle_alert(accept=False)

    def stretch(self, size=0.8):
        """
        页面放大/缩小
        :param size: 放大/缩小百分比
        """
        js = "document.body.style.zoom='{}'".format(size)
        self.driver.run_js(js)

    def release(self):
        """释放动作，无"""
        ...

    def text(self, locator, index=0, timeout=8):
        """元素文本"""
        elem = self._ele_(locator, index, timeout=timeout, count=0)  # 在批量获取时去掉闪烁不然太浪费时间。
        return elem.text

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
        """获取元素内部属性"""
        pre_sleep = kwargs.get('pre_sleep', self.SLEEP)
        raise_ = kwargs.get('raise_', False)
        elem = self._ele_(locator, index, timeout=3, raise_=raise_, pre_sleep=pre_sleep)
        if elem:
            return elem.attr(name)

    def get_property(self, name, locator, index=0):
        """获取元素对应的浏览器记录属性"""
        elem = self._ele_(locator, index=index, pre_sleep=0.5)
        return elem.property(name)

    def get_css_property(self, name, locator, index=0):
        """获取样式"""
        elem = self._ele_(locator, index, timeout=3, pre_sleep=0.5)
        return elem.style(name)

    def is_selected(self, locator, index=0):
        """可以用来检查 checkbox or radio button 是否被选中"""
        elem = self._ele_(locator, index)
        if elem:
            return elem.select
        else:
            return False

    def is_enable(self, locator, index=0, timeout=3, attr='class'):
        """是否可点击，默认+结合属性class值判断"""
        elem = self._ele_(locator, index, timeout=timeout, raise_=False)
        if not elem:
            return False
        dis_flag = ['false', 'disable']
        attr_value = elem.attr(attr)
        flag1 = flag2 = flag3 = bool(elem)
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
        self.driver.get_screenshot(file_path)

    def current_url(self):
        """当前地址"""
        return self.driver.url

    @property
    def page_source(self):
        """页面html"""
        return self.driver.html

    def quit(self):
        """退出"""
        try:
            self.driver.quit()
        except Exception:
            ...  # 'WebDriver' object has no attribute 'driver'，无伤大雅
        quit_ = "✌ 退出浏览器..."
        self.driver: ChromiumPage = None  # 销毁driver
        self.logger.info(quit_) if self.logger else print(quit_)

    def close(self):
        """关闭标签页"""
        return self.driver.close()

    def maximize_window(self, x=1920, y=1080):
        """最大化窗口"""
        return self.opt.set_argument('--window-size', f'{x},{y}')

    @property
    def switch_to(self):
        """
        切换到，无
        """
        return self.driver

    def back(self):
        """返回历史记录的前一步"""
        return self.driver.back()

    def default_content(self):
        """切回默认的frame，无"""
        return self.driver

    def forward(self):
        """前进历史记录的后一步"""
        return self.driver.forward()

    def refresh(self):
        """刷新"""
        return self.driver.refresh()

    def switch_to_frame(self, frame_reference):
        """切换frame"""
        return self.driver

    def switch_to_parent_frame(self):
        """切到父frame"""
        return self.driver

    def window_handles(self):
        """windows句柄"""
        return self.driver

    def switch_to_window(self, handle: int):
        """切换浏览器标签页"""
        self.driver.activate_tab(handle)

    def new_tab(self):
        """新开浏览器标签页"""
        self.driver.new_tab()

    def size(self, locator):
        """元素宽高"""
        ...

    def move_to_element(self, locator, index=0, timeout=3, click=False, logged=True):
        """鼠标移动到元素上(点击)"""
        elem = self._ele_(locator, index=index, timeout=timeout, logged=logged)
        if click:
            elem.hover().click()
        else:
            elem.hover()

    def offset_click(self, locator=None, x=0, y=0):
        """坐标（元素偏移）点击"""
        elem = self._ele_(locator)
        elem.offset(locator=locator, x=x, y=y).click()

    def offset_double_click(self, locator=None, x=0, y=0):
        """鼠标双击"""
        elem = self._ele_(locator)
        elem.offset(locator=locator, x=x, y=y).click()
        elem.offset(locator=locator, x=x, y=y).click()

    def hover(self, locator, index=0):
        """悬浮"""
        return self.move_to_element(locator, index=index, click=False)

    def double_click(self, locator):
        """双击"""
        return self.offset_double_click(locator)

    def right_click(self, locator, index=0, raise_=True):
        """右键点击"""
        elem = self._ele_(locator, index=index, raise_=raise_)
        ...  # 无

    def drag_and_drop(self, source, target, index1=0, index2=0):
        """元素拖拽到元素"""
        elem1 = self._ele_(source, index=index1)
        elem2 = self._ele_(target, index=index2)
        elem1.drag_to(elem2)

    def drag_and_drop_by_offset(self, locator, x, y, index=0):
        """元素拖拽至坐标，横向滚动更好用"""
        elem = self._ele_(locator=locator, index=index)
        elem.drag(offset_x=x, offset_y=y)

    def location_once_scrolled_into_view(self, locator, index=0, raise_=True):
        """滚动到元素，竖向滚动更好用"""
        return self.driver

    def run_js(self, js):
        """执行js"""
        return self.driver.run_js(script=js)

    @property
    def contains_xpath(self):
        return '//*[contains(., %s)]'

    def enter(self, locator=None, index=0):
        """按下 enter 键"""
        if locator:
            elem = self._ele_(locator, index=index)
            elem.input(Keys.ENTER)
        else:
            self.ac.input(Keys.ENTER)
            self.logger.info('✔ 按下 enter 键') if self.logger else print('✔ 按下 enter 键')

    def select_all(self, locator, index=0):
        """全选"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.input([Keys.COMMAND, "a"])
        else:
            elem.input([Keys.CONTROL, "a"])

    def cut(self, locator, index=0):
        """剪切：：ctrl+x"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.input([Keys.COMMAND, "x"])
        else:
            elem.input([Keys.CONTROL, "x"])

    def copy(self, locator, index=0):
        """复制：ctrl+c"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.input([Keys.COMMAND, "c"])
        else:
            elem.input([Keys.CONTROL, "c"])

    def paste(self, locator, index=0):
        """粘贴：ctrl+v"""
        elem = self._ele_(locator, index=index)
        if platform.system().lower() == "darwin":
            elem.input([Keys.COMMAND, "v"])
        else:
            elem.input([Keys.CONTROL, "v"])

    def backspace(self, locator, empty: bool = True):
        """按下 回格 键"""
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.input([Keys.COMMAND, "a"])
            else:
                elem.input([Keys.CONTROL, "a"])
        elem.input(Keys.BACKSPACE)

    def delete(self, locator, empty: bool = True):
        """按下 删除 键"""
        elem = self._ele_(locator)
        if empty:
            if platform.system().lower() == "darwin":
                elem.input([Keys.COMMAND, "a"])
            else:
                elem.input([Keys.CONTROL, "a"])
        elem.input(Keys.DELETE)

    def tab(self, locator):
        """按下 Tab 键"""
        elem = self._ele_(locator)
        elem.input(Keys.TAB)

    def space(self, locator):
        """按下 空格 键"""
        elem = self._ele_(locator)
        elem.input(Keys.SPACE)

    def esc(self):
        """按下 Esc 键"""
        self.ac.input(Keys.SPACE)
        self.logger.info('✔ 按下 Esc 键') if self.logger else print('✔ 按下 Esc 键')

    def press(self, *keys):
        """按下 自定义 键"""
        self.ac.input(*keys)
        self.logger.info('✔ ' + str(*keys)) if self.logger else print('✔ ' + str(*keys))

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
        'is_visible': '是否可见 ',
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


g_driver = ...


def get_driver():
    """driver实例"""
    return g_driver
