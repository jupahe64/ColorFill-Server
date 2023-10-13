import base64
import json
import mimetypes
import os.path
import re
import sys
from typing import Optional, Callable, NamedTuple, Tuple, Iterable

import aiohttp
from aiohttp import web, WSMessage
import asyncio

from aiohttp.web_request import Request
from aiohttp.web_ws import WebSocketResponse

import LevelGenerator
import numpy as np

generated_levels: list[str] = []
generated_levels_lock = asyncio.Lock()

levels_to_win = 8

remote_player_infos = {}


async def get_level(level_id):
    grid_size_x = 15 + 5 * (level_id-1)//2
    # grid_size_x = 20 - (level_id - 1)*2
    # grid_size_x = random.randint(1, 10)*5
    max_effective_moves = 15 + 5 * (level_id-1)
    # brightness = 1.0 - (level_id - 1) / levels_to_win
    brightness = 1.0

    async with generated_levels_lock:  # probably not needed
        if level_id > len(generated_levels):
            min_ratio = min(x.level_size_ratio for x in remote_player_infos.values())
            grid_size_y = int(grid_size_x*min_ratio)

            samples = [
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate(),
                LevelGenerator.Generator(grid_size_x, grid_size_y, max_effective_moves).generate()
            ]

            # get level with the most effective moves
            level = max(samples, key=lambda x: x[1])[0]
            level_str = ''.join(str(x) for x in level)
            generated_levels.append(level_str)
            level_id = len(generated_levels)
        else:
            level_str = generated_levels[level_id - 1]

    return level_id, level_str, grid_size_x, brightness


class ResultMessage(NamedTuple):
    message: str
    bg_style: str
    fg_style: str

    def to_message(self, players_left):
        message = self.message
        if players_left > 0:
            message += f"\n{players_left} players left"
        else:
            message += "\nGame complete"
        return create_message(message, self.bg_style, self.fg_style)


class PlayerInfo:
    def __init__(self, name: str, ws: WebSocketResponse):
        self.name = name
        self.socket = ws
        self.level_size_ratio = 1.0
        self.level = 0
        self.level_progress = 0.0
        self.last_progress_message = ""
        self.is_ready = False
        self.result_message: Optional[ResultMessage] = None


leaderboard_listeners = []

leaderboard_results_json: Optional[str] = None


async def send_to_all_players(message: str | Callable[[PlayerInfo], Optional[str]]):
    player: PlayerInfo
    for key, player in list(remote_player_infos.items()):
        if player.socket.closed:
            print("Closed connection with", player.name)
            del remote_player_infos[key]
            continue

        if isinstance(message, str):
            await player.socket.send_str(message)
        else:
            _message = message(player)
            if _message is not None:
                await player.socket.send_str(_message)


def create_level_message(level_id, level_name: str, grid_size_x: int, brightness: float, level_str: str):
    return f"level:{level_id};{level_name};{grid_size_x};{brightness};{level_str}"


def create_lobby_message(players: Iterable[Tuple[str, bool]]):
    players_str = "\n".join(name+("+" if ready else "-") for name, ready in players)
    return f"lobby:{players_str}"


def create_message(message, bg_style="#000", fg_style="#fff"):
    return f"message:{bg_style};{fg_style};{message}"


def create_overlay_message(message, style="#fff", display_time=1.0, animation="none"):
    return f"overlay_message:{display_time};{animation};{style};{message}"


async def end_game():
    def message(p: PlayerInfo):
        if p.result_message is not None:
            return p.result_message.to_message(0)
        else:
            return None

    await send_to_all_players(message)

    remote_player_infos.clear()
    generated_levels.clear()


def update_leaderboard_results():
    info: PlayerInfo
    results = [
        [info.name, info.level, info.level_progress, info.last_progress_message]
        for info in remote_player_infos.values()
    ]

    results.sort(key=lambda x: x[1] + x[2], reverse=True)

    for entry in results:
        if entry[1] == levels_to_win:
            entry[1] = "F"

    global leaderboard_results_json
    leaderboard_results_json = json.dumps(results)


def ready_players_count():
    return sum(1 for p in remote_player_infos.values() if p.is_ready)


def players_done_count():
    return sum(1 for p in remote_player_infos.values() if p.result_message is not None)


async def websocket_handler(request: Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    msg: WSMessage
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                player_info = remote_player_infos.get(request.remote, None)
                if player_info is not None:
                    origin = f"{player_info.name}({request.remote})"
                else:
                    origin = request.remote

                print("received", msg.data, "from", origin)

                player_info: PlayerInfo = remote_player_infos.get(request.remote, None)

                p: PlayerInfo
                all_players_ready = ready_players_count() == len(remote_player_infos)

                if ready_players_count() == 0:
                    all_players_ready = False

                match = re.match("^([a-zA-Z0-9_]*):(.*)$", msg.data)
                if match:
                    command, data = match.groups()

                    def lobby_message(self_p: PlayerInfo):
                        return create_lobby_message(
                            (p.name, p.is_ready) for p in remote_player_infos.values() if p is not self_p
                        )

                    if command == "RegisterPlayer":
                        if player_info is not None and player_info.result_message is not None:
                            await ws.send_str(player_info.result_message.to_message(
                                len(remote_player_infos) - players_done_count()
                            ))
                            continue

                        match = re.match(r"^(.*){(.*)}$", data)
                        if match:
                            player_name, extra_infos = match.groups()

                            if all_players_ready and player_info is not None:
                                level_id, level_str, grid_size_x, brightness = await get_level(max(1, player_info.level))
                                player: PlayerInfo
                                await ws.send_str(
                                    create_level_message(level_id, f"Level {level_id}",grid_size_x,brightness,level_str)
                                )
                                continue
                            elif all_players_ready and player_info is None:
                                await ws.send_str(
                                    create_message(
                                        "Game already\nin progress",
                                        bg_style="#400", fg_style="#fcc"
                                    )
                                )
                                continue

                            if player_info is None:
                                player_info = PlayerInfo(player_name, ws)
                                player_info.is_ready = all_players_ready
                                remote_player_infos[request.remote] = player_info
                            elif player_info.socket.closed:
                                player_info.socket = ws
                            else:
                                player_info.name = player_name

                            for pair in extra_infos.split(";"):
                                key, value = pair.split("=", 1)

                                if key == "levelSizeRatio":
                                    player_info.level_size_ratio = float(value)

                            await send_to_all_players(lobby_message)

                    elif command == "AnnounceReady":
                        was_all_players_ready = all_players_ready
                        player_info.is_ready = True
                        all_players_ready = all(p.is_ready for p in remote_player_infos.values())

                        if not was_all_players_ready and all_players_ready:
                            level_id, level_str, grid_size_x, brightness = await get_level(1)
                            player: PlayerInfo

                            await send_to_all_players(
                                create_level_message(level_id, f"Level {level_id}", grid_size_x, brightness, level_str)
                            )

                            for player in remote_player_infos.values():
                                player.level = level_id
                        else:
                            await send_to_all_players(lobby_message)

                    elif command == "AnnounceDone" and player_info is not None:
                        player_info.level += 1
                        level_id, level_str, grid_size_x, brightness = await get_level(player_info.level)

                        if level_id == levels_to_win+1:
                            player_info.level -= 1
                            player_info.level_progress = 1.0

                            players_done = players_done_count()

                            match players_done:
                                case 0:
                                    player_info.result_message = ResultMessage("You are #1!", "#631", "#fc4")

                                    def message(p):
                                        if p == player_info:
                                            return None
                                        else:
                                            return create_overlay_message(
                                                f"{player_info.name} is already done\nHurry up!",
                                                display_time=2.0, animation="fly-in"
                                            )

                                    await send_to_all_players(message)

                                    asyncio.ensure_future(count_down(5.0, 30))
                                case 1:
                                    player_info.result_message = ResultMessage("You are #2", "#334", "#eef4ff")
                                case 2:
                                    player_info.result_message = ResultMessage("You are #3", "#521", "#fa7")
                                case _:
                                    player_info.result_message = ResultMessage(f"You are #{players_done + 1}",
                                                                               "#034", "#cfd")

                            players_left = len(remote_player_infos) - players_done_count()

                            def message(p: PlayerInfo):
                                if p.result_message is not None:
                                    return p.result_message.to_message(players_left)
                                else:
                                    return None

                            await send_to_all_players(message)

                            update_leaderboard_results()

                            if players_done_count() == len(remote_player_infos):
                                await end_game()

                            continue

                        await ws.send_str(
                            create_level_message(level_id, f"Level {level_id}", grid_size_x, brightness, level_str)
                        )

                    elif command == "AnnounceProgress" and player_info is not None:
                        match = re.match("^(\\d+);(\\d+);(.*)$", data)
                        if match:
                            grid_size_x = int(match[1])
                            grid_size_y = int(match[2])
                            compressed_level_bytes = np.frombuffer(base64.b64decode(match[3]), dtype='uint8')

                            level_bytes = np.zeros(shape=(len(compressed_level_bytes), 4), dtype='uint8')

                            level_bytes[:, 0] |= compressed_level_bytes & 0b11
                            level_bytes[:, 1] |= (compressed_level_bytes >> 2) & 0b11
                            level_bytes[:, 2] |= (compressed_level_bytes >> 4) & 0b11
                            level_bytes[:, 3] |= (compressed_level_bytes >> 6)

                            empty_count = np.count_nonzero(level_bytes == 0)
                            filled_count = np.count_nonzero(level_bytes == 2)

                            player_info.level_progress = filled_count / (empty_count+filled_count)
                            player_info.last_progress_message = data

                            update_leaderboard_results()

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    return ws


async def websocket_handler_leaderboard(request: Request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    leaderboard_listeners.append(ws)

    msg: WSMessage
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    return ws


async def file_handler(path):
    print(f"loading file {path}")
    if not os.path.exists(path):
        print("FAILED")
        # leaderboard_page_res_path = "Live-Leaderboard/public/"+path
        # if os.path.exists(leaderboard_page_res_path):
        #     return await file_handler(leaderboard_page_res_path)
        # else:
        return web.Response(status=404)

    with open(path, 'rb') as file:
        return web.Response(body=file.read(), content_type=mimetypes.guess_type(path)[0])


async def any_file_handler(request: Request):
    path = request.path[1:]
    referring_page = request.cookies.get("referringPage")

    if referring_page == "Client":
        path = "ColorFill-Client/public/" + path
    elif referring_page == "Leaderboard":
        path = "Live-Leaderboard/public/" + path
    return await file_handler(path)


def create_runner():
    app = web.Application()
    app.add_routes([
        web.get('/', lambda x: file_handler("ColorFill-Client/public/index.html")),
        web.get('/leaderboard', lambda x: file_handler("Live-Leaderboard/public/index.html")),
        web.get('/ws', websocket_handler),
        web.get('/leaderboard/ws', websocket_handler_leaderboard),
        web.get('/{tail:.*}', any_file_handler),
    ])
    return web.AppRunner(app)


async def start_server(host="0.0.0.0", port=8000):
    runner = create_runner()
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print("server started on", host, f"port={port}")


async def count_down(delay, number=30):
    await asyncio.sleep(delay)
    while number > 10:
        if players_done_count() == len(remote_player_infos):
            return

        def message(p: PlayerInfo):
            if p.result_message is None:
                return create_overlay_message(f"{number} seconds left!", display_time=2.0,
                                              animation="fly-in")

        await send_to_all_players(message)

        await asyncio.sleep(10)
        number -= 10

    while number > 0:
        if players_done_count() == len(remote_player_infos):
            return

        def message(p: PlayerInfo):
            if p.result_message is None:
                if number <= 3:
                    return create_overlay_message(f"  {number}  ", style="#f88")
                else:
                    return create_overlay_message(f"   {number}   ")

        await send_to_all_players(message)

        await asyncio.sleep(1)
        number -= 1

    if players_done_count() == len(remote_player_infos):
        return

    def message(p: PlayerInfo):
        if p.result_message is None:
            return create_message("Game over", bg_style="#300", fg_style="#f00")

    await send_to_all_players(message)

    await end_game()


async def publish_results():
    while True:
        await asyncio.sleep(0.1)

        if leaderboard_results_json is not None:
            for listener in leaderboard_listeners:
                listener: WebSocketResponse
                if listener.closed:
                    continue
                await listener.send_str(leaderboard_results_json)

        leaderboard_listeners[:] = [x for x in leaderboard_listeners if not x.closed]


if __name__ == "__main__":
    asyncio.ensure_future(start_server(sys.argv[1], int(sys.argv[2])))
    asyncio.ensure_future(publish_results())

    loop = asyncio.get_event_loop()
    loop.run_forever()
