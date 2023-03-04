import asyncio
import contextlib
import time
import threading
import typing as T
import uvicorn

if T.TYPE_CHECKING:
    from fastapi import FastAPI
    from disnake.ext.commands import Bot


class Server(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


def run_app_and_bot(app: "FastAPI", bot: "Bot", token: str) -> None:
    config = uvicorn.Config(app, host="127.0.0.1", port=5000, log_level="info")
    server = Server(config=config)
    
    with server.run_in_thread():
        bot.run(token)
