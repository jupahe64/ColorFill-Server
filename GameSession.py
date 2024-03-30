from typing import List, Tuple

import LevelGenerator
from common import IGameSession, IParticipant, LevelProgress, Level

def generate_level(level_id: int, min_ratio: float):
    grid_size_x = 15 + 5 * (level_id - 1) // 2
    # grid_size_x = 20 - (level_id - 1)*2
    # grid_size_x = random.randint(1, 10)*5
    max_effective_moves = 15 + 5 * (level_id - 1)
    # brightness = 1.0 - (level_id - 1) / levels_to_win
    brightness = 1.0

    grid_size_y = int(grid_size_x * min_ratio)

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

    return Level(level_id, level_str, grid_size_x, brightness)


class GameSession(IGameSession):
    def __init__(self):
        self.participants: List[IParticipant] = []
        self.levels: List[Level] = []
        self.min_ratio = float('inf')

    def join(self, participant: IParticipant, level_size_ratio: float):
        self.min_ratio = min(self.min_ratio, level_size_ratio)
        self.participants.append(participant)
        pass

    def leave(self, participant: IParticipant):
        pass

    def _start_game(self):
        pass




    def announce_level_progress(self, participant: IParticipant, progress: LevelProgress):
        pass

    def announce_done(self, participant: IParticipant):
        pass
