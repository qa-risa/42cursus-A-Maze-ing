from mazegen.maze_generator import (
    MazeGeneratorBasic
)
import random


class MazeGenerator(MazeGeneratorBasic):
    """
    再帰的バックトラッキング法を用いた迷路生成クラス。
    """
    def maze_gen(self) -> None:
        """
        迷路の生成(recursive backtrack) を実行する。
        """
        for _ in range(1000):
            self.reset()
            # 42のセルから始めると42に穴があくので、42以外から選ぶ
            candidates = [
                (x, y)
                for x in range(self._config.WIDTH)
                for y in range(self._config.HEIGHT)
                if not self._pos[x][y].is_42
            ]
            start = random.choice(candidates)
            self._parent: dict[
                tuple[int, int], tuple[int, int] | None
            ] = {start: None}
            self.change_to_visited(start)
            self.backtrack(start)
            if not self._config.PERFECT:
                self.make_non_complete_maze()
            # 3x3の開けた空間がなければ完成
            if not self.check_big_space():
                return
        raise ValueError("could not generate a maze without 3x3 open area")

    def backtrack(self, start: tuple[int, int]) -> None:
        """
        再帰的に壁を破壊し迷路を生成する。

        Args:
            start (tuple[int, int]): 現在探索中の座標。
        """
        while True:
            non_visited = self.get_non_visited_cardinal(start)
            # スタート地点に戻り、進める方向もなければ完成
            if not non_visited and self._parent[start] is None:
                return
            if non_visited:
                cardinal = random.choice(non_visited)
                self.break_wall(start, str(cardinal))
                self.append_parent(str(cardinal), start, self._parent)
                new_position = self.get_new_position(start, str(cardinal))
                self.change_to_visited(new_position)
            else:
                new_position = self.get_old_position(start, self._parent)
                self.pop_parent(start, self._parent)
            start = new_position

    def get_non_visited_cardinal(self, position: tuple[int, int]) -> list[str]:
        """
        未訪問の隣接する方向を取得する。

        Args:
            position (tuple[int, int]): 現在の座標。

        Returns:
            list[str]: 未訪問の方向のリスト。
        """
        x, y = position
        non_visited = []
        if y > 0 and not self._pos[x][y - 1].visited:
            non_visited.append("N")
        if x < self._config.WIDTH - 1 and not self._pos[x + 1][y].visited:
            non_visited.append("E")
        if y < self._config.HEIGHT - 1 and not self._pos[x][y + 1].visited:
            non_visited.append("S")
        if x > 0 and not self._pos[x - 1][y].visited:
            non_visited.append("W")
        return non_visited

    def append_parent(
        self, cardinal: str, position: tuple[int, int],
        parent: dict[tuple[int, int], tuple[int, int] | None]
    ) -> dict[tuple[int, int], tuple[int, int] | None]:
        """
        移動先セルの親として現在のセルを登録する。

        Args:
            cardinal (str): 移動方向。
            position (tuple[int, int]): 現在の座標。
            parent (dict): 親情報を管理する辞書。

        Returns:
            dict: 更新された親情報の辞書。
        """
        x, y = position
        if cardinal == "N":
            parent[(x, y - 1)] = (x, y)
        if cardinal == "E":
            parent[(x + 1, y)] = (x, y)
        if cardinal == "S":
            parent[(x, y + 1)] = (x, y)
        if cardinal == "W":
            parent[(x - 1, y)] = (x, y)
        return parent

    def get_new_position(
        self, position: tuple[int, int], cardinal: str
    ) -> tuple[int, int]:
        """
        指定された方向に進んだ際の新しい座標を計算する。

        Args:
            position (tuple[int, int]): 現在の座標。
            cardinal (str): 移動する方向。

        Returns:
            tuple[int, int]: 新しい座標。
        """
        x, y = position
        new_x = x
        new_y = y
        if cardinal == "N":
            new_x = x
            new_y = y - 1
        if cardinal == "E":
            new_x = x + 1
            new_y = y
        if cardinal == "S":
            new_x = x
            new_y = y + 1
        if cardinal == "W":
            new_x = x - 1
            new_y = y
        return (new_x, new_y)

    def pop_parent(
        self, position: tuple[int, int],
        parent: dict[tuple[int, int], tuple[int, int] | None]
    ) -> dict[tuple[int, int], tuple[int, int] | None]:
        """
        辞書から指定された座標の親情報を削除する。

        Args:
            position (tuple[int, int]): 削除対象の座標。
            parent (dict): 親情報を管理する辞書。

        Returns:
            dict: 更新された親情報の辞書。
        """
        x, y = position
        parent.pop((x, y))
        return parent

    def get_old_position(
        self, position: tuple[int, int],
        parent: dict[tuple[int, int], tuple[int, int] | None]
    ) -> tuple[int, int]:
        """
        親情報を参照して1つ前の座標を取得する。

        Args:
            position (tuple[int, int]): 現在の座標。
            parent (dict): 親情報を管理する辞書。

        Returns:
            tuple[int, int]: 親（1つ前）の座標。
        """
        old_position = parent[position]
        if old_position is None:
            return position
        return old_position

    def check_all_visited(self) -> bool:
        """
        全てのセルが訪問済みか確認する。

        Returns:
            bool: 全てのセルを訪問していればTrue、そうでなければFalse。
        """
        result = True
        for x in range(self._config.WIDTH):
            for y in range(self._config.HEIGHT):
                result &= self._pos[x][y].visited
        return result


if __name__ == "__main__":
    from mazegen.maze_generator import Config
    config = Config(
        WIDTH=20, HEIGHT=20, ENTRY=(0, 0), EXIT=(19, 19),
        OUTPUT_FILE="dummy.txt"
    )
    maze = MazeGenerator(config)
    print("= 迷路生成前 =")
    maze.maze_show()
    print("= 迷路生成後 =")
    maze.maze_gen()
    maze.maze_show()
