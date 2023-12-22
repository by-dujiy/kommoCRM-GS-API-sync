import logging
import inspect


# exception logger set up
error_logger = logging.getLogger('exceptions_log')
fh = logging.FileHandler('error.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s\n'
    )
)
error_logger.addHandler(fh)
error_logger.setLevel(logging.WARNING)


# debug logger set up
debug_logger = logging.getLogger('debug_logger')
stream_log = logging.StreamHandler()
stream_log.setFormatter(logging.Formatter(
    '%(asctime)s - %(message)s\n'
    )
)
debug_logger.addHandler(stream_log)
debug_logger.setLevel(logging.INFO)


def exc_log(e):
    caller_function_name = inspect.stack()[1].function
    message = f"[{caller_function_name}] occur exception: {e}"
    error_logger.error(message, exc_info=True)


def call_log(*args):
    func_name = inspect.stack()[1].function
    msg = f"CALL   - [{func_name}] with args:\n\t =>>> {args}"
    debug_logger.info(msg)


def result_log(res):
    func_name = inspect.stack()[1].function
    msg = f"RESULT - [{func_name}]:\n\t ===> {res}\n"
    debug_logger.info(msg)
