import logging


class DummyLogger(logging.Logger):
    def log(self, level, msg, *args, **kwargs):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass
