import itertools
import json
import mimetypes
import os.path
import re
from typing import Optional

import aiohttp
from aiohttp import web, WSMessage
import asyncio

from aiohttp.abc import BaseRequest
from aiohttp.web_request import Request
from aiohttp.web_ws import WebSocketResponse

import LevelGenerator

generated_levels: list[str] = []
generated_levels_lock = asyncio.Lock()

gridSizeX = 30
gridSizeY = 0xFFFFFFFF

remote_player_infos = {}


class PlayerInfo:
    def __init__(self, name, ws):
        self.name = name
        self.socket = ws
        self.level_size_ratio = 1.0
        self.level = 0
        self.level_progress = 0.0
        self.is_ready = False


leaderboard_listeners = []

leaderboard_results_json: Optional[str] = None


async def get_level(level_id):
    async with generated_levels_lock:  # probably not needed
        if level_id > len(generated_levels):
            level = LevelGenerator.Generator(gridSizeX, 15).generate()
            level_str = ''.join(str(x) for x in level)
            generated_levels.append(level_str)
            level_id = len(generated_levels)
        else:
            level_str = generated_levels[level_id - 1]

    return level_id, level_str


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
                ready_players_count = sum(1 for p in remote_player_infos.values() if p.is_ready)
                all_players_ready = ready_players_count == len(remote_player_infos)

                if ready_players_count == 0:
                    all_players_ready = False

                global gridSizeY

                match = re.match("^([a-zA-Z0-9_]*):(.*)$", msg.data)
                if match:
                    command, data = match.groups()

                    if command == "RegisterPlayer":
                        match = re.match("^(.*)\\[(.*)]$", data)
                        if match:
                            player_name, extra_infos = match.groups()

                            if not player_info:
                                player_info = PlayerInfo(player_name, ws)
                                player_info.is_ready = all_players_ready
                                remote_player_infos[request.remote] = player_info
                            elif player_info.socket.closed:
                                player_info.socket = ws

                            for pair in extra_infos.split(";"):
                                key, value = pair.split("=", 1)

                                if key == "levelSizeRatio":
                                    player_info.level_size_ratio = float(value)

                                    gridSizeY = min(gridSizeY, int(round(float(value) * gridSizeX)))

                            if all_players_ready:
                                level_id, level_str = await get_level(max(1, player_info.level))
                                player: PlayerInfo
                                await ws.send_str(f"level:{level_id};{gridSizeX};{level_str}")
                            else:
                                for key, player in list(remote_player_infos.items()):
                                    if player.socket.closed:
                                        del remote_player_infos[key]
                                        continue
                                    await player.socket.send_str(f"lobby:{ready_players_count}/{len(remote_player_infos)}")

                    elif command == "AnnounceReady":
                        was_all_players_ready = all_players_ready
                        player_info.is_ready = True
                        all_players_ready = all(p.is_ready for p in remote_player_infos.values())

                        if not was_all_players_ready and all_players_ready:
                            level_id, level_str = await get_level(1)
                            player: PlayerInfo

                            for key, player in list(remote_player_infos.items()):
                                if player.socket.closed:
                                    del remote_player_infos[key]
                                    continue
                                await player.socket.send_str(f"level:{level_id};{gridSizeX};{level_str}")
                                player.level = 1

                    elif command == "RequestLevel" and player_info is not None and re.match("^\\d+$", data):
                        level_id = int(data)

                        level_id, level_str = await get_level(level_id)
                        await ws.send_str(f"level:{level_id};{gridSizeX};{level_str}")

                        try:
                            player_info.level = int(data)

                        except TypeError:
                            pass
                    elif command == "AnnounceProgress" and player_info is not None and re.match("^\\d+/\\d+$", data):
                        player_info.level_progress = eval(data)  # should be fine

                        info: PlayerInfo
                        results = [
                            [info.name, info.level, info.level_progress]
                            for info in remote_player_infos.values()
                        ]

                        results.sort(key=lambda x: x[1]+x[2], reverse=True)

                        global leaderboard_results_json
                        leaderboard_results_json = json.dumps(results)

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
        leaderboard_page_res_path = "Live-Leaderboard/public/"+path
        if os.path.exists(leaderboard_page_res_path):
            return await file_handler(leaderboard_page_res_path)
        else:
            return web.Response(status=404)

    with open(path, 'rb') as file:
        return web.Response(body=file.read(), content_type=mimetypes.guess_type(path)[0])


async def any_file_handler(request: Request):
    path = request.path[1:]
    return await file_handler(path)


def create_runner():
    app = web.Application()
    app.add_routes([
        web.get('/', lambda x: file_handler("index.html")),
        web.get('/leaderboard', lambda x: file_handler("Live-Leaderboard/public/index.html")),
        web.get('/ws', websocket_handler),
        web.get('/leaderboard/ws', websocket_handler_leaderboard),
        web.get('/{tail:.*}', any_file_handler),
    ])
    return web.AppRunner(app)


async def start_server(host="192.168.137.1", port=8000):
    runner = create_runner()
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()


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
    asyncio.ensure_future(start_server())
    asyncio.ensure_future(publish_results())

    loop = asyncio.get_event_loop()
    loop.run_forever()
