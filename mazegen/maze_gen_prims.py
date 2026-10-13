from mazegen.maze_generator import (
    MazeGeneratorBasic
)
import random


class MazeGeneratorPrims(MazeGeneratorBasic):
    """ランダム化Prim法を使って迷路を生成するクラス。"""

    def maze_gen(self) -> None:
        """
        全域木となる迷路を生成する。

        PERFECT=False の場合は、その後さらに壁を壊して
        ループを持つ迷路へ変更する。
        """
        for _ in range(1000):
            self.reset()
            self._build_once()
            # 3x3の開けた空間がなければ完成
            if not self.check_big_space():
                return
        raise ValueError("could not generate a maze without 3x3 open area")

    def _build_once(self) -> None:
        """
        迷路を1回組み立てる(3x3の確認は呼び出し側で行う)。
        """
        start = self._choose_start()
        self.change_to_visited(start)

        frontier: list[
            tuple[tuple[int, int], str, tuple[int, int]]
        ] = []

        self._add_frontier(start, frontier)

        while frontier:
            index = random.randrange(len(frontier))

            frontier[index], frontier[-1] = (
                frontier[-1],
                frontier[index],
            )

            current, cardinal, target = frontier.pop()
            tx, ty = target

            if self._pos[tx][ty].visited:
                continue

            self.break_wall(current, cardinal)
            self.change_to_visited(target)
            self._add_frontier(target, frontier)

        if not self._config.PERFECT:
            self.make_non_complete_maze()

    def _choose_start(self) -> tuple[int, int]:
        """
        42パターン以外から、開始セルをランダムに1つ選ぶ。

        Returns:
            tuple[int, int]: 選ばれた開始セルの座標。

        Raises:
            ValueError: 有効なセルが存在しない場合。
        """
        candidates = [
            (x, y)
            for x in range(self._config.WIDTH)
            for y in range(self._config.HEIGHT)
            if not self._pos[x][y].is_42
        ]

        if not candidates:
            raise ValueError(
                "迷路生成に使用できるセルがありません"
            )

        index = random.randrange(len(candidates))

        return candidates[index]

    def _add_frontier(
        self,
        position: tuple[int, int],
        frontier: list[
            tuple[
                tuple[int, int],
                str,
                tuple[int, int],
            ]
        ],
    ) -> None:
        """
        訪問済みセルから未訪問の隣接セルへ伸びる辺を
        frontierへ追加する。

        Args:
            position (tuple[int, int]): 追加の起点となるセルの座標。
            frontier (list): 辺を追加する対象のリスト。
        """
        x, y = position

        neighbours = (
            ("N", (x, y - 1)),
            ("E", (x + 1, y)),
            ("S", (x, y + 1)),
            ("W", (x - 1, y)),
        )

        for cardinal, (nx, ny) in neighbours:
            if not (
                0 <= nx < self._config.WIDTH
            ):
                continue

            if not (
                0 <= ny < self._config.HEIGHT
            ):
                continue

            if (
                self._pos[nx][ny].visited
                or self._pos[nx][ny].is_42
            ):
                continue

            frontier.append(
                (
                    position,
                    cardinal,
                    (nx, ny),
                )
            )
