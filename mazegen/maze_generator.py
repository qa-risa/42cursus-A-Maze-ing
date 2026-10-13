#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator
import random


class Config(BaseModel):
    """
    config.txtを格納するクラス

    各KEYに対するVALUEにそれぞれ条件をつけてvalidationを行う
    """
    WIDTH: int = Field(ge=3)
    HEIGHT: int = Field(ge=3)
    ENTRY: tuple[int, int]
    EXIT: tuple[int, int]
    OUTPUT_FILE: str = Field(min_length=1)
    PERFECT: bool = Field(default=False)
    SEED: int = Field(default=42)
    STRATEGY: str = Field(default="recursive")
    MAX_DEAD_ENDS: int = Field(default=0, ge=0)

    @field_validator("PERFECT", mode="before")
    @classmethod
    def parse_perfect(cls: Any, v: Any) -> Any:
        """
        PERFECTはTrueかFalseだけを受け付ける。

        pydanticは"yes"や"1"もboolにしてしまうので、ここで制限する。

        Args:
            v (Any): パースする値。

        Returns:
            Any: bool、または元の値。

        Raises:
            ValueError: TrueでもFalseでもない場合。
        """
        if isinstance(v, str):
            if v.lower() == "true":
                return True
            if v.lower() == "false":
                return False
            raise ValueError("PERFECT must be True or False")
        return v

    @field_validator("STRATEGY", mode="before")
    @classmethod
    def check_strategy(cls: Any, v: Any) -> Any:
        """
        STRATEGYが対応しているアルゴリズム名か確認する。

        Args:
            v (Any): 確認する値。

        Returns:
            Any: 小文字にした名前。

        Raises:
            ValueError: 対応していない名前の場合。
        """
        if isinstance(v, str):
            v = v.lower()
        if v not in ("recursive", "prims", "kruskals"):
            raise ValueError("STRATEGY must be recursive, prims or kruskals")
        return v

    @field_validator("ENTRY", "EXIT", mode="before")
    @classmethod
    def parse_pos(cls: Any, v: Any) -> Any:
        """
        ENTRY, EXITをタプルに変換する。

        変換できない形式ならそのまま返す。

        Args:
            v (Any): パースする値。

        Returns:
            Any: 変換済みのタプル、または元の値。
        """
        if isinstance(v, str):
            parts = v.split(",")
            # 「x,y」の2つの整数でなければエラーにする
            if len(parts) != 2:
                raise ValueError("must be two integers like 0,0")
            try:
                return (int(parts[0]), int(parts[1]))
            except ValueError:
                raise ValueError("must be two integers like 0,0")
        return v

    @model_validator(mode='after')
    def check_entry_and_exit(self) -> "Config":
        """
        Entry, Exitの妥当性の検証を行う。

        以下のいずれかに該当すればエラーを投げる
        ・Entry, Exitが同じ場所にある
        ・Entry, Exitが迷路の範囲外に存在する

        Returns:
            Config: バリデーションに成功したConfigインスタンス。

        Raises:
            ValueError: 座標が同じ、または範囲外の場合。
        """
        entry_x, entry_y = self.ENTRY
        exit_x, exit_y = self.EXIT

        if self.ENTRY == self.EXIT:
            raise ValueError("Entry and exit should be different")
        if not (0 <= entry_x < self.WIDTH and 0 <= entry_y < self.HEIGHT):
            raise ValueError("Entry should be inside the maze bounds")
        if not (0 <= exit_x < self.WIDTH and 0 <= exit_y < self.HEIGHT):
            raise ValueError("Exit should be inside the maze bounds")
        return self


class Cell(BaseModel):
    """
    迷路の1マス（セル）の状態を管理するクラス。

    Attributes:
        value (int): 壁の状態を示す16進数値 (0-15)。
        visited (bool): 迷路生成時に訪問済みかどうか。
        is_42 (bool): '42'のパターンの一部かどうか。
        is_min (bool): 最短経路の一部かどうか。
    """
    value: int = Field(ge=0, le=15)
    visited: bool = Field(default=False)
    is_42: bool = Field(default=False)
    is_min: bool = Field(default=False)


class MazeGeneratorBasic(ABC):
    """
    迷路生成アルゴリズムのベースとなる抽象クラス。
    """
    _config: Config
    _pos: list[list[Cell]]
    _parent: dict[tuple[int, int], tuple[int, int] | None]
    _bonus: bool
    _history: list[tuple[tuple[int, int], str]]
    _exist_42: bool

    def __init__(self, config: Config) -> None:
        """
        初期化関数。

        ・self._configにconfig.txtを格納
        ・self._posに座標データを入れる。15で初期化(全方面に壁が存在)。
        ・rondom.seed(self._config.SEED)で初期化。
        """
        self._config = config
        self.reset()
        # 入口・出口が42の閉じたセルの上にあると、たどり着けない
        for name, (x, y) in (("ENTRY", config.ENTRY),
                             ("EXIT", config.EXIT)):
            if self._pos[x][y].is_42:
                raise ValueError(f"{name} is inside the '42' pattern")

    def reset(self) -> None:
        """
        迷路の初期状態をセットする。
        """
        self._pos = [
            [Cell(value=15, visited=False)
             for _ in range(self._config.HEIGHT)]
            for _ in range(self._config.WIDTH)
        ]
        self._exist_42 = False
        self.make_42_pattern()
        self._parent = {}
        self._bonus = False
        self._history = []

    def maze_show(self) -> None:
        """
        迷路の可視化を行う。

        標準出力に16進数で迷路の壁状態を表示させる。
        """
        for y in range(self._config.HEIGHT):
            for x in range(self._config.WIDTH):
                print(f"{self._pos[x][y].value:x}", end="")
            print()

    def break_wall(self, position: tuple[int, int], cardinal: str) -> None:
        """
        壁を破壊する。

        座標,方角を引数に取り、その方角の壁を破壊する。

        Args:
            position (tuple[int, int]): 対象となるセルの座標。
            cardinal (str): 破壊する壁の方向 ('N', 'E', 'S', 'W')。

        Raises:
            ValueError: 無効な方角が指定された場合。
        """
        x, y = position
        if cardinal == "N":
            self._pos[x][y].value -= 8
            self._pos[x][y - 1].value -= 2
        elif cardinal == "E":
            self._pos[x][y].value -= 4
            self._pos[x + 1][y].value -= 1
        elif cardinal == "S":
            self._pos[x][y].value -= 2
            self._pos[x][y + 1].value -= 8
        elif cardinal == "W":
            self._pos[x][y].value -= 1
            self._pos[x - 1][y].value -= 4
        else:
            raise ValueError("break_wall(): cardinal should be N, E, S or W")
        self._history.append(((position), cardinal))

    def is_road(self, pos: tuple[int, int], n_pos: tuple[int, int]) -> bool:
        """
        隣接する2つのセル間に道が開通しているか判定する。

        Args:
            pos (tuple[int, int]): 基準となるセルの座標。
            n_pos (tuple[int, int]): 隣接するセルの座標。

        Returns:
            bool: 道が開通していればTrue、そうでなければFalse。
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

    def change_to_visited(self, position: tuple[int, int]) -> None:
        """
        座標(x, y)のvisitedステータスをTrueに変更する。

        Args:
            position (tuple[int, int]): 訪問済みにするセルの座標。
        """
        x, y = position
        self._pos[x][y].visited = True

    def make_42_pattern(self) -> None:
        """
        迷路内に '42' のパターンを初期生成する。
        """
        if self._config.WIDTH < 9 or self._config.HEIGHT < 7:
            return
        if self._config.WIDTH % 2 == 0:
            self.make_42_pattern_even()
            self._exist_42 = True
        if self._config.WIDTH % 2 == 1:
            self.make_42_pattern_odd()
            self._exist_42 = True

    def make_42_pattern_even(self) -> None:
        """
        偶数幅の迷路用に '42' のパターンを生成する。
        """
        pattern_42 = [
            [True, False, False, False, False, True, True, True],
            [True, False, False, False, False, False, False, True],
            [True, True, True, False, False, True, True, True],
            [False, False, True, False, False, True, False, False],
            [False, False, True, False, False, True, True, True]
        ]
        width_42 = 8
        height_42 = 5
        width_start = (self._config.WIDTH - 8) // 2
        height_start = (self._config.HEIGHT - 5) // 2
        for x, nx in enumerate(range(width_start, width_start + width_42)):
            for y, ny in enumerate(range(height_start,
                                         height_start + height_42)):
                self._pos[nx][ny].visited = pattern_42[y][x]
                self._pos[nx][ny].is_42 = pattern_42[y][x]

    def make_42_pattern_odd(self) -> None:
        """
        奇数幅の迷路用に '42' のパターンを生成する。
        """
        pattern_42 = [
            [True, False, False, False, True, True, True],
            [True, False, False, False, False, False, True],
            [True, True, True, False, True, True, True],
            [False, False, True, False, True, False, False],
            [False, False, True, False, True, True, True]
        ]
        width_42 = 7
        height_42 = 5
        width_start = (self._config.WIDTH - 7) // 2
        height_start = (self._config.HEIGHT - 5) // 2
        for x, nx in enumerate(range(width_start, width_start + width_42)):
            for y, ny in enumerate(range(height_start,
                                         height_start + height_42)):
                self._pos[nx][ny].visited = pattern_42[y][x]
                self._pos[nx][ny].is_42 = pattern_42[y][x]

    def make_non_complete_maze(self) -> None:
        """
        不要な行き止まりを破壊して、不完全な（ループのある）迷路を生成する。
        """
        # 残してよい行き止まりの数はconfigのMAX_DEAD_ENDSで決める
        keep_dead_end = self.pick_dead_end_to_keep(
            self._config.MAX_DEAD_ENDS
        )
        self.break_center_and_corners()
        changed = True
        while changed:
            changed = False
            for x in range(self._config.WIDTH):
                for y in range(self._config.HEIGHT):
                    if (x, y) in keep_dead_end:
                        continue
                    if self.break_dead_end(x, y):
                        changed = True

    def break_dead_end(self, x: int, y: int) -> bool:
        """
        行き止まりの壁をランダムな方向へ1つ破壊する。

        Args:
            x (int): X座標。
            y (int): Y座標。

        Returns:
            bool: 壁を破壊した場合はTrue、そうでなければFalse。
        """
        if self._pos[x][y].is_42:
            return False

        value = self._pos[x][y].value
        open_count = 4 - bin(value).count("1")
        if open_count != 1:
            return False

        cardinals = []
        if (y > 0 and value & 8 == 8 and
                not self._pos[x][y - 1].is_42):
            cardinals.append("N")
        if (x < self._config.WIDTH - 1 and value & 4 == 4 and
                not self._pos[x + 1][y].is_42):
            cardinals.append("E")
        if (y < self._config.HEIGHT - 1 and value & 2 == 2 and
                not self._pos[x][y + 1].is_42):
            cardinals.append("S")
        if (x > 0 and value & 1 == 1 and
                not self._pos[x - 1][y].is_42):
            cardinals.append("W")

        if not cardinals:
            return False

        cardinal = random.choice(cardinals)
        self.break_wall((x, y), str(cardinal))
        return True

    def pick_dead_end_to_keep(
        self, max_dead_end: int
    ) -> list[tuple[int, int]]:
        """
        残しておく行き止まりのセルをランダムに選択する。

        Args:
            max_dead_end (int): 残す行き止まりの最大数。

        Returns:
            list[tuple[int, int]]: 残す行き止まりの座標のリスト。
        """
        if max_dead_end <= 0:
            return []

        candidates = []
        for x in range(self._config.WIDTH):
            for y in range(self._config.HEIGHT):
                if self._pos[x][y].is_42:
                    continue
                open_count = 4 - bin(self._pos[x][y].value).count("1")
                if open_count == 1:
                    candidates.append((x, y))
        if not candidates:
            return []

        pick_count = min(len(candidates), max_dead_end)

        index = random.sample(range(len(candidates)), pick_count)
        return [candidates[int(i)] for i in index]

    def check_big_space(self) -> bool:
        """
        迷路内に3x3の開けた空間が存在するか確認する。

        3x3の範囲の内側の壁(東の壁6本と南の壁6本)が
        すべて開いていれば、3x3の開けた空間とみなす。

        Returns:
            bool: 広い空間が存在する場合はTrue、そうでなければFalse。
        """
        for left in range(self._config.WIDTH - 2):
            for top in range(self._config.HEIGHT - 2):
                if self.is_open_3x3(left, top):
                    return True
        return False

    def is_open_3x3(self, left: int, top: int) -> bool:
        """
        (left, top)を左上とする3x3の範囲が全部開いているか確認する。

        Args:
            left (int): 左上のX座標。
            top (int): 左上のY座標。

        Returns:
            bool: 内側の壁が1本もなければTrue。
        """
        for dx in range(3):
            for dy in range(3):
                value = self._pos[left + dx][top + dy].value
                # 右端の列以外は、東の壁(4)があれば開けていない
                if dx < 2 and value & 4:
                    return False
                # 下端の行以外は、南の壁(2)があれば開けていない
                if dy < 2 and value & 2:
                    return False
        return True

    def break_center_and_corners(self) -> None:
        """
        パックマン用に迷路の四隅と中心の壁を破壊する。
        """
        if self._pos[0][0].value & 4 == 4:
            self.break_wall((0, 0), "E")
        if self._pos[0][0].value & 2 == 2:
            self.break_wall((0, 0), "S")
        if self._pos[0][self._config.HEIGHT - 1].value & 8 == 8:
            self.break_wall((0, self._config.HEIGHT - 1), "N")
        if self._pos[0][self._config.HEIGHT - 1].value & 4 == 4:
            self.break_wall((0, self._config.HEIGHT - 1), "E")
        if self._pos[self._config.WIDTH - 1][0].value & 1 == 1:
            self.break_wall((self._config.WIDTH - 1, 0), "W")
        if self._pos[self._config.WIDTH - 1][0].value & 2 == 2:
            self.break_wall((self._config.WIDTH - 1, 0), "S")

        if (self._pos[self._config.WIDTH - 1]
                [self._config.HEIGHT - 1].value & 8 == 8):
            self.break_wall(
                (self._config.WIDTH - 1, self._config.HEIGHT - 1), "N"
            )
        if (self._pos[self._config.WIDTH - 1]
                [self._config.HEIGHT - 1].value & 1 == 1):
            self.break_wall(
                (self._config.WIDTH - 1, self._config.HEIGHT - 1), "W"
            )

        x1 = self._config.WIDTH // 2
        y1 = self._config.HEIGHT // 2

        if 0 <= x1 < self._config.WIDTH and 0 <= y1 < self._config.HEIGHT:
            if self._config.WIDTH % 2 == 0 and self._config.HEIGHT % 2 == 0:
                cells = [
                    (x1 - 1, y1 - 1), (x1, y1 - 1), (x1 - 1, y1), (x1, y1)
                    ]
                for x, y in cells:
                    if (x + 1, y) in cells and (self._pos[x][y].value & 4):
                        self.break_wall((x, y), "E")
                    if (x, y + 1) in cells and (self._pos[x][y].value & 2):
                        self.break_wall((x, y), "S")

            elif self._config.WIDTH % 2 == 0:
                if (x1 > 0 and
                        (self._pos[x1 - 1][y1].value & 4)):
                    self.break_wall((x1 - 1, y1), "E")

            elif self._config.HEIGHT % 2 == 0:
                if (y1 > 0 and
                        (self._pos[x1][y1 - 1].value & 2)):
                    self.break_wall((x1, y1 - 1), "S")

    def output_to_file(self, path_cardinal: str = "") -> None:
        """
        生成された迷路をファイルに出力する。

        Args:
            path_cardinal (str): 最短経路を示す方角の文字列。
        """
        # 自分の規約(N=8,E=4,S=2,W=1)を仕様の規約(N=1,E=2,S=4,W=8)に変換するテーブル
        # (4bitのビット順を丸ごと反転するだけで変換できる)
        REVERSE_NIBBLE = [
            0, 8, 4, 12, 2, 10, 6, 14,
            1, 9, 5, 13, 3, 11, 7, 15
        ]

        with open(self._config.OUTPUT_FILE, "w") as f:
            for y in range(self._config.HEIGHT):
                for x in range(self._config.WIDTH):
                    spec_value = REVERSE_NIBBLE[self._pos[x][y].value]
                    f.write(f"{spec_value:x}")
                f.write("\n")
            f.write("\n")
            entry_x, entry_y = self._config.ENTRY
            exit_x, exit_y = self._config.EXIT
            f.write(f"{entry_x},{entry_y}\n")
            f.write(f"{exit_x},{exit_y}\n")
            f.write(f"{path_cardinal}\n")

    @abstractmethod
    def maze_gen(self) -> None:
        """
        迷路生成の抽象メソッド。各アルゴリズムで実装する。
        """
        ...


if __name__ == "__main__":
    # 実行するときはmaze_gen()メソッドをコメントアウト
    maze_gen_inst = MazeGeneratorBasic()  # type: ignore
    print("= 迷路の初期化 =")
    maze_gen_inst.maze_show()
    print("= break_wall()の検証 =")
    maze_gen_inst.break_wall((1, 1), "N")
    maze_gen_inst.break_wall((3, 3), "E")
    maze_gen_inst.break_wall((6, 6), "S")
    maze_gen_inst.break_wall((9, 9), "W")
    maze_gen_inst.maze_show()
