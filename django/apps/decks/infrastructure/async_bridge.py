"""Ponte estável entre entrypoints síncronos do Django e repositórios Motor."""

import asyncio
import os
import threading
from functools import wraps


class PersistentAsyncExecutor:
    """Executa corrotinas em um único event loop daemon por processo."""

    def __init__(self):
        self._state_lock = threading.Lock()
        self._loop = None
        self._thread = None
        self._pid = None

    @staticmethod
    def _serve(loop, ready):
        asyncio.set_event_loop(loop)
        ready.set()
        loop.run_forever()

    def _get_loop(self):
        process_id = os.getpid()

        with self._state_lock:
            if (
                self._pid != process_id
                or self._loop is None
                or self._thread is None
                or not self._thread.is_alive()
            ):
                ready = threading.Event()
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(
                    target=self._serve,
                    args=(self._loop, ready),
                    daemon=True,
                    name="mongo-event-loop",
                )
                self._pid = process_id
                self._thread.start()
                ready.wait()

            return self._loop

    def run(self, coroutine):
        loop = self._get_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        return future.result()


_executor = PersistentAsyncExecutor()


def persistent_async_to_sync(async_callable):
    """Mantém a interface de ``async_to_sync(func)(*args)`` já usada."""

    @wraps(async_callable)
    def wrapper(*args, **kwargs):
        return _executor.run(async_callable(*args, **kwargs))

    return wrapper
