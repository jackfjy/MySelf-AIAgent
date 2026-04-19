import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def summarize(text: str, max_len: int = 200) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ")
    return text[:max_len] + ("..." if len(text) > max_len else "")

def log_node(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            if logger.isEnabledFor(logging.DEBUG):
                arg_preview = []
                for arg in args:
                    if isinstance(arg, str):
                        arg_preview.append(summarize(arg))
                    else:
                        arg_preview.append(f"<{type(arg).__name__}>")

                kwargs_preview = {}
                for k, v in kwargs.items():
                    if isinstance(v, str):
                        kwargs_preview[k] = summarize(v)
                    else:
                        kwargs_preview[k] = f"<{type(v).__name__}>"

                logger.debug(f"[{name}] inputs args={arg_preview} kwargs={kwargs_preview}")

            result = func(*args, **kwargs)

            cost = (time.time() - start_time) * 1000

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"[{name}] result={summarize(result)}")
                logger.debug(f"[{name}] cost={cost:.2f}ms")

            return result
        return wrapper
    return decorator