from mazegen.maze_generator import (
    MazeGeneratorBasic
)
import random


class DisjointSet:
    """サイクルを効率よく検出するためのUnion-Find構造。"""

    _parent: dict[tuple[int, int], tuple[int, int]]
    _rank: dict[tuple[int, int], int]

    def __init__(
        self,
        nodes: list[tuple[int, int]],
    ) -> None:
        """
        すべての迷路セルを、それぞれ独立した集合として初期化する。

        Args:
            nodes (list[tuple[int, int]]): 迷路のセルのリスト。
        """
        self._parent = {
            node: node
            for node in nodes
        }

        self._rank = {
            node: 0
            for node in nodes
        }

    def find(
        self,
        node: tuple[int, int],
    ) -> tuple[int, int]:
        """
        経路圧縮を行いながら、その集合の代表要素を返す。

        Args:
            node (tuple[int, int]): 対象のセル座標。

        Returns:
            tuple[int, int]: 代表となるセルの座標。
        """
        parent = self._parent[node]

        if parent != node:
            self._parent[node] = self.find(parent)

        return self._parent[node]

    def union(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
    ) -> bool:
        """
        2つの集合を結合する。

        すでに同じ集合に属していた場合はFalseを返す。

        Args:
            first (tuple[int, int]): 1つ目のセル座標。
            second (tuple[int, int]): 2つ目のセル座標。

        Returns:
            bool: 結合に成功した場合はTrue、既に同じ集合ならFalse。
        """
        root_a = self.find(first)
        root_b = self.find(second)

        if root_a == root_b:
            return False

        rank_a = self._rank[root_a]
        rank_b = self._rank[root_b]

        if rank_a < rank_b:
            self._parent[root_a] = root_b

        elif rank_a > rank_b:
            self._parent[root_b] = root_a

        else:
            self._parent[root_b] = root_a
            self._rank[root_a] += 1

        return True


class MazeGeneratorKruskals(MazeGeneratorBasic):
    """ランダム化Kruskal法を使って迷路を生成するクラス。"""

    def maze_gen(self) -> None:
        """
        全域木となる迷路を生成する。

        PERFECT=False の場合は、その後さらに壁を壊して
        ループのある迷路にする。
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
        cells = [
            (x, y)
            for x in range(self._config.WIDTH)
            for y in range(self._config.HEIGHT)
            if not self._pos[x][y].is_42
        ]

        if not cells:
            raise ValueError(
                "迷路生成に使用できるセルがありません"
            )

        edges = self._build_edges()

        order = list(range(len(edges)))
        random.shuffle(order)

        sets = DisjointSet(cells)

        for raw_index in order:
            index = int(raw_index)

            first, cardinal, second = (
                edges[index]
            )

            if sets.union(first, second):
                self.break_wall(
                    first,
                    cardinal,
                )

        for x, y in cells:
            self.change_to_visited(
                (x, y)
            )

        if not self._config.PERFECT:
            self.make_non_complete_maze()

    def _build_edges(
        self,
    ) -> list[
        tuple[
            tuple[int, int],
            str,
            tuple[int, int],
        ]
    ]:
        """
        42以外の隣接セル間の辺を、それぞれ1回だけ作成する。

        Returns:
            list: 作成されたエッジのリスト。
        """
        edges: list[
            tuple[
                tuple[int, int],
                str,
                tuple[int, int],
            ]
        ] = []

        for x in range(self._config.WIDTH):
            for y in range(self._config.HEIGHT):
                if self._pos[x][y].is_42:
                    continue

                if x + 1 < self._config.WIDTH:
                    if not self._pos[x + 1][y].is_42:
                        edges.append(
                            (
                                (x, y),
                                "E",
                                (x + 1, y),
                            )
                        )

                if y + 1 < self._config.HEIGHT:
                    if not self._pos[x][y + 1].is_42:
                        edges.append(
                            (
                                (x, y),
                                "S",
                                (x, y + 1),
                            )
                        )

        return edges
