import logging
from enum import Enum


class Color(Enum):
    BLACK = "\u001b[30m"
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
    BLUE = "\u001b[34m"
    MAGENTA = "\u001b[35m"
    CYAN = "\u001b[36m"
    WHITE = "\u001b[37m"
    RESET = "\u001b[0m"

    @staticmethod
    def colorize(text: str, color: "Color"):
        return color.value + text + Color.RESET.value


COLORS = {
    "CRITICAL": Color.RED,
    "ERROR": Color.RED,
    "WARNING": Color.YELLOW,
    "INFO": Color.CYAN,
    "DEBUG": Color.WHITE,
}


class Logger(logging.Logger):
    def __init__(self):
        super().__init__("BOT", logging.DEBUG)
        self.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = Formatter()
        handler.setFormatter(formatter)
        self.addHandler(handler)


class Formatter(logging.Formatter):
    def __init__(self):
        super().__init__("{asctime} [{levelname}] {name}: {message}", style="{")

    def format(self, record: logging.LogRecord):
        color = COLORS[record.levelname]
        record.levelname = Color.colorize(record.levelname, color)
        return super().format(record)
