import inspect
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from enum import Enum
from json import JSONEncoder
from logging import getLevelName

_LOGGER_INIT_INFO = None

LEVELS = {
    logging.DEBUG: "DEBUG",
    logging.INFO: "INFO",
    logging.WARN: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}


class SimpleEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value


class JsonFormatter(logging.Formatter):
    def format(self, rec):  # noqa
        message_name = rec.getMessage()
        log = {
            "@timestamp": datetime.utcfromtimestamp(rec.created).isoformat()
            + "Z",
            "message": message_name,
            "fields": {
                "pid": rec.process,
                "thread": rec.thread,
                "type": LEVELS.get(rec.levelno)[0],
                "log_level": LEVELS.get(rec.levelno),
                "name": rec.name,
                "line_no": rec.lineno,
                "process_name": rec.processName,
                "thread_name": rec.threadName,
            },
        }

        if rec.exc_info:
            e_type, value, tb = rec.exc_info
            log["error"] = {
                "name": message_name,
                "message": repr(value),
                "traceback": "".join(
                    traceback.format_exception(e_type, value, tb)
                ),
            }
        return json.dumps(log, cls=SimpleEncoder, ensure_ascii=False)


def init_logger(is_debug: bool = False, name: str = "", level: str = "INFO"):
    is_debug = (
        os.getenv("DEVELOPMENT") == "1"
        or os.getenv("DEBUG") == "1"
        or is_debug
    )
    # The logger can only be initialized once
    global _LOGGER_INIT_INFO
    prev_frame = inspect.stack()[1]
    if _LOGGER_INIT_INFO is not None:
        raise RuntimeError(
            f"Attempt to reinitialization the logger. "
            f"Current call from {prev_frame.filename} line {prev_frame.lineno}. "
            f"First call from {_LOGGER_INIT_INFO['filename']} line {_LOGGER_INIT_INFO['lineno']}"
        )
    _LOGGER_INIT_INFO = {
        "filename": prev_frame.filename,
        "lineno": prev_frame.lineno,
    }

    logger = logging.getLogger(name)
    logger.handlers = []
    log_handler = logging.StreamHandler()
    if is_debug:
        log_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.setLevel(logging.DEBUG)
    else:
        log_handler.stream = sys.stdout
        log_handler.setFormatter(JsonFormatter())
        logger.setLevel(getLevelName(level))

        def except_hook(*args):
            exc_type, value, current_traceback = args
            formatted_traceback = "".join(
                traceback.format_exception(exc_type, value, current_traceback)
            )
            logger.critical(formatted_traceback, exc_info=True)

        sys.excepthook = except_hook
    logger.addHandler(log_handler)

    return logger


def get_logger(module, name=None):
    logger_fqn = module
    if name is not None:
        if inspect.isclass(name):
            name = name.__name__
        logger_fqn += "." + name
    logger = logging.getLogger(logger_fqn)
    return logger
