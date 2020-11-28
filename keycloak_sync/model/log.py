"""Custom log for keycloak synchronize tool"""
import logging
import sys
LOG_LEVEL = "INFO"


class KCLogFormatter(logging.Formatter):
    """Declare a new logging formatter."""

    MAX_NAME_LENGTH = 20

    def format(self, record):
        date = self.formatTime(record).replace(",", ".")
        levelname = record.levelname
        message = record.getMessage()
        name = record.name

        prefix = name[: self.MAX_NAME_LENGTH - 1]
        suffix = (
            name[self.MAX_NAME_LENGTH - 1:]
            if len(name) <= self.MAX_NAME_LENGTH
            else "\u2026"
        )
        name = f"{prefix}{suffix}".ljust(self.MAX_NAME_LENGTH)
        log = f"[{date}][{name}] {levelname.ljust(8)} {message}"

        return log


class _MaxLevelFilter:
    def __init__(self, highest_log_level):
        self._highest_log_level = highest_log_level

    def filter(self, log_record):
        return log_record.levelno <= self._highest_log_level


class _ApplicationFilter:
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, log_record):
        return (
            log_record.name.startswith(
                self.app_name) or log_record.name == "__main__"
        )


class _LibraryFilter:
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, log_record):
        return not (
            log_record.name.startswith(
                self.app_name) or log_record.name == "__main__"
        )


_app_name = __name__.split(".")[0]

# A handler for logs from the app
app_info_handler = logging.StreamHandler(sys.stdout)
app_info_handler.setLevel(LOG_LEVEL)
app_info_handler.addFilter(_MaxLevelFilter(logging.WARNING))
app_info_handler.addFilter(_ApplicationFilter(_app_name))

# A handler for logs from libraries
lib_info_handler = logging.StreamHandler(sys.stdout)
lib_info_handler.setLevel(logging.INFO)
lib_info_handler.addFilter(_MaxLevelFilter(logging.WARNING))
lib_info_handler.addFilter(_LibraryFilter(_app_name))

# A handler for high level logs that should be sent to STDERR
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setLevel(logging.ERROR)

# formatter
formatter = KCLogFormatter()
app_info_handler.setFormatter(formatter)
lib_info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.DEBUG, handlers=[
        app_info_handler, lib_info_handler, error_handler]
)
