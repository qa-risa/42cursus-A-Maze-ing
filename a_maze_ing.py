#!/usr/bin/env python3
import sys
import random
from typing import Any
from pydantic import ValidationError
from mazegen.maze_generator import Config
from mazegen import MazeGenerator
from mazegen.maze_gen_prims import MazeGeneratorPrims
from mazegen.maze_gen_kruskals import MazeGeneratorKruskals
from mazegen.bfs import BreadthFirstSearch
from mazegen.visualizer import Visualizer


# 必須キーの一覧
MANDATORY_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}


def parse_config(path: str) -> Config:
    """
    config.txtのパースを行う。

    1行ずつ読み、KEY=VALUEの形式かを確認してConfigにして返す。

    Args:
        path (str): 設定ファイルのパス。

    Returns:
        Config: パースされた設定オブジェクト。

    Raises:
        ValueError: 形式が正しくない、必須キーがない場合。
        OSError: ファイルが開けない場合。
    """
    pairs: dict[str, Any] = {}
    with open(path) as f:
        for num, raw in enumerate(f, start=1):
            line = raw.strip()
            # 空行と「#」で始まる行はコメントとして無視する
            if line == "" or line.startswith("#"):
                continue
            # 「=」がない行はKEY=VALUE形式ではないのでエラー
            if "=" not in line:
                raise ValueError(f"line {num}: '{line}' is not KEY=VALUE")
            key, value = line.split("=", 1)
            key = key.strip().upper()  # 小文字のキーも受け付ける
            value = value.strip()
            if key == "" or value == "":
                raise ValueError(f"line {num}: empty key or value")
            if key in pairs:
                raise ValueError(f"line {num}: duplicate key '{key}'")
            pairs[key] = value
    # 必須キーがすべてあるか確認する
    missing = MANDATORY_KEYS - pairs.keys()
    if missing:
        raise ValueError(f"missing key(s): {', '.join(sorted(missing))}")
    return Config(**pairs)


def main() -> None:
    """
    main関数

    STRATEGYによって迷路生成アルゴリズムを切り替える
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    config = parse_config(sys.argv[1])
    maze = MazeGenerator(config)
    random.seed(maze._config.SEED)

    if maze._config.STRATEGY == "recursive":
        maze.maze_gen()
        bfs = BreadthFirstSearch(maze._pos, maze._config)
        bfs.search_maze()
        maze.output_to_file(bfs._path_cardinal)
        visualizer = Visualizer(
            bfs._pos, bfs._config, bfs._path,
            maze._history, bfs._history_bfs, maze._exist_42
        )
        visualizer.visualize()
        visualizer.show()
    elif maze._config.STRATEGY == "prims":
        maze_prims = MazeGeneratorPrims(config)
        maze_prims.maze_gen()
        bfs_prims = BreadthFirstSearch(
            maze_prims._pos, maze_prims._config
        )
        bfs_prims.search_maze()
        maze_prims.output_to_file(bfs_prims._path_cardinal)
        vis_prims = Visualizer(
            bfs_prims._pos, bfs_prims._config, bfs_prims._path,
            maze_prims._history, bfs_prims._history_bfs,
            maze_prims._exist_42
        )
        vis_prims.visualize()
        vis_prims.show()
    elif maze._config.STRATEGY == "kruskals":
        maze_kruskals = MazeGeneratorKruskals(config)
        maze_kruskals.maze_gen()
        bfs_kruskals = BreadthFirstSearch(
            maze_kruskals._pos, maze_kruskals._config
        )
        bfs_kruskals.search_maze()
        maze_kruskals.output_to_file(bfs_kruskals._path_cardinal)
        vis_kruskals = Visualizer(
            bfs_kruskals._pos, bfs_kruskals._config, bfs_kruskals._path,
            maze_kruskals._history, bfs_kruskals._history_bfs,
            maze_kruskals._exist_42
        )
        vis_kruskals.visualize()
        vis_kruskals.show()


if __name__ == "__main__":
    try:
        main()
    except ValidationError as e:
        # pydanticの検証エラー。どのキーが悪いかを短く表示する
        for err in e.errors():
            key = ".".join(str(loc) for loc in err["loc"]) or "config"
            print(f"[Error] {key}: {err['msg']}")
        sys.exit(1)
    except (OSError, ValueError) as e:
        # ファイルが開けない、形式が正しくない場合など
        print(f"[Error] {e}")
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C や Ctrl+D で終了したとき
        print("\nBye")
        sys.exit(0)
