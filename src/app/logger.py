import atexit
import json
import logging
import logging.config
import logging.handlers
import pathlib
import queue
import re

log_queue = queue.Queue(-1)


class JSONFormatter(logging.Formatter):
    def __init__(
        self, field_map: dict[str, str] | None = None, datefmt: str | None = None
    ) -> None:
        super().__init__(datefmt=datefmt)
        self.field_map = field_map or {}

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        output = {}

        for output_name, record_attr in self.field_map.items():
            if record_attr == "asctime":
                value = self.formatTime(record, self.datefmt)
            else:
                value = getattr(record, record_attr, None)

            output[output_name] = value

        if record.exc_info:
            output["exception"] = self.formatException(record.exc_info)

        return json.dumps(output, ensure_ascii=False)


class NonErrorFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.WARNING


class RedactFilter(logging.Filter):
    REDACT_KEYS = {"password", "token", "api_key", "secret", "authorization"}
    REPLACEMENT = "[REDACTED]"

    VALUE_PATTERNS = [
        re.compile(r"\b\d{16}\b"),  # credit card
    ]

    def _redact_value(self, value):
        if isinstance(value, str):
            for p in self.VALUE_PATTERNS:
                value = p.sub(self.REPLACEMENT, value)
            return value

        if isinstance(value, dict):
            return {
                k: self.REPLACEMENT
                if k.lower() in self.REDACT_KEYS
                else self._redact_value(v)
                for k, v in value.items()
            }

        if isinstance(value, list):
            return [self._redact_value(v) for v in value]

        return value

    def filter(self, record: logging.LogRecord) -> bool:
        # redact message
        msg = record.getMessage()
        msg = self._redact_value(msg)
        record.msg = msg
        record.args = ()

        # redact extra fields
        for key, value in record.__dict__.items():
            if key.lower() in self.REDACT_KEYS:
                record.__dict__[key] = self.REPLACEMENT
            else:
                record.__dict__[key] = self._redact_value(value)

        return True


def setup_logging(config_path="logging_config.json"):
    cfg = json.loads(pathlib.Path(config_path).read_text())
    logging.config.dictConfig(cfg)

    file_h = logging._handlers["file"]
    stderr_h = logging._handlers["stderr"]

    listener = logging.handlers.QueueListener(
        log_queue,
        file_h,
        stderr_h,
        respect_handler_level=True,
    )

    listener.start()
    atexit.register(listener.stop)


# usage in your application entrypoint:
# from app.logger import setup_logging
# setup_logging("logging_config.json")
# logger = logging.getLogger(__name__)
# logger.info("startup", extra={"request_id": "xyz"})
