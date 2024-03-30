import json
import re
from typing import Callable, NamedTuple, Union, List, Protocol

import aiohttp
from aiohttp import WSMessage
from aiohttp.web_ws import WebSocketResponse


class Lobby(NamedTuple):
    class Player(NamedTuple):
        name: str
        isReady: bool

    players: List[Player]


class Level(NamedTuple):
    id: int
    name: str
    string: str
    width: int
    brightness: float


class LevelProgress(NamedTuple):
    width: int
    height: int
    string: str


class FullScreenText:
    text: str
    bg_fill_style: str
    fg_fill_style: str


class OverlayText:
    text: str
    fill_style: str
    duration: int
    animation: str


SOCKET_MESSAGE = Union[Lobby, Level, FullScreenText, OverlayText]


class PlayerInfo(NamedTuple):
    name: str
    level_size_ratio: float


class IParticipant(Protocol):
    def on_game_ended(self):
        pass


class IGameSession(Protocol):
    def join(self, participant: IParticipant, level_size_ratio: float):
        pass

    def leave(self, participant: IParticipant):
        pass

    def announce_level_progress(self, participant: IParticipant, progress: LevelProgress):
        pass

    def announce_done(self, participant: IParticipant):
        pass


class IGameManager(Protocol):
    def get_or_create_game(self):
        pass

    def close_game(self):
        pass


class SocketWrapper:
    def __init__(self, ws: WebSocketResponse):
        self.ws = ws
        self.on_register_player_received: Callable[[PlayerInfo], None] | None = None
        self.on_change_name_received: Callable[[str], None] | None = None
        self.on_announce_ready_received: Callable[[], None] | None = None
        self.on_announce_progress_received: Callable[[LevelProgress], None] | None = None
        self.on_announce_done_received: Callable[[], None] | None = None

        msg: WSMessage
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                continue
            if msg.data == 'close':
                await ws.close()
                continue

            match = re.match(r"^([a-zA-Z0-9_]*)(?::([\s\S]*))?$", msg.data)
            if not match:
                continue

            command, data = match.groups()

            if command == "RegisterPlayer":
                player_info = json.loads(data)

                if self.on_register_player_received:
                    name: str = player_info["name"]
                    self.on_register_player_received(
                        PlayerInfo(name.replace("\n", ""), player_info["levelSizeRatio"])
                    )

            elif command == "ChangeName":
                if self.on_change_name_received:
                    self.on_change_name_received(data.replace("\n", ""))
            elif command == "AnnounceReady":
                if self.on_announce_ready_received:
                    self.on_announce_ready_received()
            elif command == "AnnounceProgress":
                if self.on_announce_ready_received:
                    width, height, string = re.match(r"^([0-9]+);;([0-9]+);([-A-Za-z0-9+/=]*)$", data)
                    self.on_announce_progress_received(
                        LevelProgress(int(width), int(height), string)
                    )
            elif command == "AnnounceDone":
                if self.on_announce_done_received:
                    self.on_announce_done_received()

    def send_lobby(self, lobby: Lobby):
        players_str = "\n".join(name + ("+" if ready else "-") for name, ready in lobby.players)
        self.ws.send_str(f"lobby:{players_str}")

    def send_level(self, level: Level):
        self.ws.send_str(f"level:{level.id};{level.name};{level.width};{level.brightness};{level.string}")

    def send_full_screen_text(self, t: FullScreenText):
        self.ws.send_str(f"message:{t.bg_fill_style};{t.fg_fill_style};{t.text}")

    def send_overlay_text(self, t: OverlayText):
        self.ws.send_str(f"overlay_message:{t.duration};{t.animation};{t.fill_style};{t.text}")

    def send_message(self, message: SOCKET_MESSAGE):
        if isinstance(message, Lobby):
            self.send_lobby(message)
        elif isinstance(message, Level):
            self.send_level(message)
        elif isinstance(message, FullScreenText):
            self.send_full_screen_text(message)
        elif isinstance(message, OverlayText):
            self.send_overlay_text(message)

