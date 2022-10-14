class Log:

    def __init__(self, logger=None):
        self.logger = logger

    def info(self, s):
        return self.logger.info(s) if self.logger else print(s)

    def warning(self, s):
        return self.logger.warning(s) if self.logger else print(s)

    def error(self, s):
        return self.logger.error(s) if self.logger else print(s)
