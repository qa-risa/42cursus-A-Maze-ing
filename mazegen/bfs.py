#!/usr/bin/env python3

from mazegen.maze_generator import Config, Cell
from mazegen.maze_gen_recursive import MazeGenerator
from collections import deque


class BreadthFirstSearch:
    """
    幅優先探索アルゴリズムを用いて迷路の最短経路を探索するクラス。
    """
    _pos: list[list[Cell]]
    _config: Config
    _path: list[tuple[int, int]]
    _path_cardinal: str
    _history_bfs: list[tuple[tuple[int, int], tuple[int, int] | None]]

    def __init__(self, pos: list[list[Cell]], config: Config) -> None:
        """
        BreadthFirstSearchクラスを初期化する。

        Args:
            pos (list[list[Cell]]): 迷路のセル情報を持つ2次元リスト。
            config (Config): 迷路の設定。
        """
        self._pos = pos
        self._config = config
        self._path = []
        self._path_cardinal = ""
        self._history_bfs = []

    def search_maze(self) -> None:
        """
        幅優先探索により、迷路のスタートからゴールまでの最短経路を探索する。
        """
        start: tuple[int, int] = (
            int(self._config.ENTRY[0]), int(self._config.ENTRY[1])
        )
        goal: tuple[int, int] = (
            int(self._config.EXIT[0]), int(self._config.EXIT[1])
        )

        queue: deque[tuple[int, int]] = deque([start])
        visited: set[tuple[int, int]] = {start}
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

        while queue:
            x, y = queue.popleft()
            if (x, y) == goal:
                path = self.reconstruct_path(parent, goal)
                self._path = path
                self._path_cardinal = self.make_path_cardinal(path)
                # self.show(self._path_cardinal)
                return
            self._history_bfs.append(((x, y), parent[(x, y)]))
            cardinals = self.get_passible_cardinals(x, y)
            if not cardinals:
                continue
            for cardinal in cardinals:
                nx, ny = self.get_position_based_on_cardinal(x, y, cardinal)
                if (nx, ny) not in visited and self.is_road((x, y), (nx, ny)):
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    queue.append((nx, ny))
        return

    def get_passible_cardinals(self, x: int, y: int) -> list[str]:
        """
        現在の座標から移動可能な方角を取得する。

        Args:
            x (int): X座標。
            y (int): Y座標。

        Returns:
            list[str]: 移動可能な方角 ('N', 'E', 'S', 'W') のリスト。
        """
        cardinals = ["N", "E", "S", "W"]
        if y < 1:
            cardinals.remove("N")
        if x > self._config.WIDTH - 2:
            cardinals.remove("E")
        if y > self._config.HEIGHT - 2:
            cardinals.remove("S")
        if x < 1:
            cardinals.remove("W")
        return cardinals

    def get_position_based_on_cardinal(
        self, x: int, y: int, cardinal: str
    ) -> tuple[int, int]:
        """
        指定された方角に進んだ場合の新しい座標を取得する。

        Args:
            x (int): 現在のX座標。
            y (int): 現在のY座標。
            cardinal (str): 進む方向 ('N', 'E', 'S', 'W')。

        Returns:
            tuple[int, int]: 移動先の座標。
        """
        if cardinal == "N":
            return (x, y - 1)
        if cardinal == "E":
            return (x + 1, y)
        if cardinal == "S":
            return (x, y + 1)
        if cardinal == "W":
            return (x - 1, y)
        return (x, y)

    def reconstruct_path(
        self,
        parent: dict[tuple[int, int], tuple[int, int] | None],
        goal: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """
        親セルの記録からスタートからゴールまでの経路を復元する。

        Args:
            parent (dict): 各セルから親セルへのマッピング。
            goal (tuple[int, int]): ゴールの座標。

        Returns:
            list[tuple[int, int]]: 復元された経路の座標リスト。
        """
        path = []
        node: tuple[int, int] | None = goal
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
        return path

    def make_path_cardinal(self, path: list[tuple[int, int]]) -> str:
        """
        座標のリストから方角の文字列を生成する。

        Args:
            path (list[tuple[int, int]]): 経路の座標リスト。

        Returns:
            str: 経路を表す方角の文字列。
        """
        path_cardinal = []
        len_path = len(path)
        for i in range(len_path - 1):
            node1 = path[i]
            node2 = path[i + 1]
            x_1, y_1 = node1
            x_2, y_2 = node2
            if y_2 < y_1:
                path_cardinal.append("N")
            if x_2 > x_1:
                path_cardinal.append("E")
            if y_2 > y_1:
                path_cardinal.append("S")
            if x_2 < x_1:
                path_cardinal.append("W")
        return "".join(path_cardinal)

    def is_road(self, pos: tuple[int, int], n_pos: tuple[int, int]) -> bool:
        """
        2つの隣接するセル間に道が開通しているか判定する。

        Args:
            pos (tuple[int, int]): 基準となるセル。
            n_pos (tuple[int, int]): 隣接するセル。

        Returns:
            bool: 開通していればTrue、そうでなければFalse。
        """
        x, y = pos
        nx, ny = n_pos
        distance = (x - nx) ** 2 + (y - ny) ** 2
        if distance != 1:
            return False
        # ビット定義: N=8, E=4, S=2, W=1
        if (ny < y and (self._pos[x][y].value & 8) == 0 and
                (self._pos[nx][ny].value & 2) == 0):
            return True
        if (nx > x and (self._pos[x][y].value & 4) == 0 and
                (self._pos[nx][ny].value & 1) == 0):
            return True
        if (ny > y and (self._pos[x][y].value & 2) == 0 and
                (self._pos[nx][ny].value & 8) == 0):
            return True
        if (nx < x and (self._pos[x][y].value & 1) == 0 and
                (self._pos[nx][ny].value & 4) == 0):
            return True
        return False

    def show(self, path_cardinal: str) -> None:
        """
        最短経路の方角文字列を出力する。

        Args:
            path_cardinal (str): 出力する文字列。
        """
        print(path_cardinal)


if __name__ == "__main__":
    config = Config(
        WIDTH=20, HEIGHT=20, ENTRY=(0, 0), EXIT=(19, 19),
        OUTPUT_FILE="dummy.txt"
    )
    maze = MazeGenerator(config)
    print("= 迷路生成前 =")
    maze.maze_show()
    print("= 迷路生成後（バックトラッキング） =")
    maze.maze_gen()
    maze.maze_show()
    print("= 最小経路探索（幅優先）=")
    bfs = BreadthFirstSearch(maze._pos, maze._config)
    bfs.search_maze()
