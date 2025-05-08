import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries: int = 3, delay: int = 1):
    """
    Yeniden deneme mekanizması dekoratörü.
    
    Args:
        max_retries (int): Maksimum yeniden deneme sayısı
        delay (int): Başlangıç bekleme süresi (saniye)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {str(e)}")
                        raise

                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s: {str(e)}")
                    await asyncio.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff

            return None

        return wrapper
    return decorator 