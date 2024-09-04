IS_LOGIN = False
PAGE: WebDriver = ...


class BasePage:
    def __init__(self, login=True):
        """
        driver实例化 + 登录
        :param login: 是否要登录，为测试登录留的参数
        """
        self.options = []
        if USE_USER_DATA:
            user_data_dir = r'user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data - 副本'
            options = [user_data_dir]
            if not os.path.exists(user_data_dir[14:]):
                options.remove(user_data_dir)

        experimental_option = {
            'prefs': {
                'download.default_directory': OUTPUT_DIR
            }
        }
        global PAGE, IS_LOGIN
        if PAGE is ...:  # 第一次
            PAGE = WebDriver(options=self.options, experimental_option=experimental_option, logger=log)
        elif not PAGE.driver:  # quit之后销毁了driver，不quit的话可以继续用driver（注意前置状态）
            PAGE = WebDriver(options=self.options, experimental_option=experimental_option, logger=log)
            IS_LOGIN = False
        self.page = PAGE

        if login:
            self.login()
            IS_LOGIN = True