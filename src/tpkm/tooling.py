import logging


class DummyLogger(logging.Logger):
    def log(self, level, msg, *args, **kwargs):  # noqa: Vulture
        pass

    def debug(self, msg, *args, **kwargs):  # noqa: Vulture
        pass

    def warning(self, msg, *args, **kwargs):  # noqa: Vulture
        pass

    def error(self, msg, *args, **kwargs):  # noqa: Vulture
        pass

    def critical(self, msg, *args, **kwargs):  # noqa: Vulture
        pass

    def info(self, msg, *args, **kwargs):  # noqa: Vulture
        pass
