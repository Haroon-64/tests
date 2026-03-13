import atexit
import json
import logging
import logging.config
import logging.handlers


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


# optional: example non-error filter (keeps only INFO and below)
class NonErrorFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.WARNING


def setup_logging(config_path: str = "logging_config.json") -> None:
    import json as _json
    import pathlib

    cfg = _json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    logging.config.dictConfig(cfg)

    # find the QueueHandler instance that dictConfig created
    root = logging.getLogger()
    q_handler = None
    for h in root.handlers:
        if isinstance(h, logging.handlers.QueueHandler):
            q_handler = h
            break

    # dictConfig constructs handler instances in logging._handlers keyed by name;
    # retrieve the named handlers to attach to the listener
    file_h = logging._handlers.get("file")
    stderr_h = logging._handlers.get("stderr")

    # If queue handler exists, start listener thread
    if q_handler and file_h:
        q = q_handler.queue
        listener = logging.handlers.QueueListener(
            q,
            *(h for h in (file_h, stderr_h) if h is not None),
            respect_handler_level=True,
        )
        listener.start()
        atexit.register(listener.stop)


# usage in your application entrypoint:
# from my_logging import setup_logging
# setup_logging("logging_config.json")
# logger = logging.getLogger(__name__)
# logger.info("startup", extra={"request_id": "xyz"})
