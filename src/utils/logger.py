from logging import getLogger, StreamHandler, Formatter


class Logger:
    def __init__(self, name, level="INFO"):
        self.logger = getLogger(name)
        self.logger.setLevel(level)
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s %(levelname)s %(message)s"))
        self.logger.addHandler(handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)
