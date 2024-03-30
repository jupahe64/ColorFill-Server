from aiohttp.web_ws import WebSocketResponse

from common import SocketWrapper


class Player:
    def __init__(self, socket: SocketWrapper, ):
        self.socket = socket

    def _on_name_change(self, name: str):
        self.name = name