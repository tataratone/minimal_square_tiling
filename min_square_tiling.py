import sys
from functools import lru_cache
import math
import pprint
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


# 同じ引数で呼び出したときはメモ化
@lru_cache(maxsize=None)
def solve(l, s):
    # 長辺 l、短辺 s の長方形を正方形で埋めるのに必要な最小枚数と分割チェーンの親の情報を返す

    # すでに正方形なら自明に1
    if l == s:
        return 1, ("X", None)

    # 互いに素でないなら gcd で割った結果と同じ
    g = math.gcd(l, s)
    if g > 1:
        cnt, _ = solve(l // g, s // g)
        return cnt, ("G", g)

    best = 10**9
    parent = None

    # 長辺分割（長い辺を l を k と l-k に割る）
    for k in range(1, l // 2 + 1):
        # 縦 >= 横 に正規化
        c1, _ = solve(max(k, s), min(k, s))
        c2, _ = solve(max(l - k, s), min(l - k, s))
        # より良ければ更新
        if c1 + c2 < best:
            best = c1 + c2
            parent = ("L", k)

    # 水平分割（横方向に b を k と b-k に割る）
    for k in range(1, s // 2 + 1):
        # 縦 >= 横 に正規化
        c1, _ = solve(max(l, k), min(l, k))
        c2, _ = solve(max(l, s - k), min(l, s - k))
        # より良ければ更新
        if c1 + c2 < best:
            best = c1 + c2
            parent = ("S", k)

    return best, parent


def reconstruct(l, s, rotated=False):
    # 回転情報を反映した座標方向に応じたサイズに変換
    size = (s, l) if rotated else (l, s)

    # 親情報から分割ツリーを生成
    cnt, (op, val) = solve(l, s)
    if op == "X":  # 葉
        return {
            "divide": "Self",
            "size": size,
            "pos": None,
            "rect1": None,
            "rect2": None,
        }
    if op == "G":  # 既約
        g = val
        sub = reconstruct(l // g, s // g, rotated)
        return scale_tree(sub, g)
    if op == "L":  # 長辺で分割
        k = val
        # 正規化と回転情報の更新
        if k < s:
            rect1 = reconstruct(s, k, not rotated)
        else:
            rect1 = reconstruct(k, s, rotated)
        if l - k < s:
            rect2 = reconstruct(s, l - k, not rotated)
        else:
            rect2 = reconstruct(l - k, s, rotated)
        return {
            "divide": "Long",
            "size": size,
            "pos": k,
            "rect1": rect1,
            "rect2": rect2,
        }
    if op == "S":  # 短辺で分割
        k = val
        # 大小関係や回転は維持される
        rect1 = reconstruct(l, k, rotated)
        rect2 = reconstruct(l, s - k, rotated)
        return {
            "divide": "Short",
            "size": size,
            "pos": k,
            "rect1": rect1,
            "rect2": rect2,
        }


def scale_tree(tree, g):
    """ツリー情報を gcd に応じて修正"""
    l, s = tree["size"]
    if tree["divide"] == "Self":
        return {
            "divide": "Self",
            "size": (l * g, s * g),
            "pos": None,
            "rect1": None,
            "rect2": None,
        }
    # 再帰的に全辺長を g 倍
    return {
        "size": (l * g, s * g),
        "divide": tree["divide"],
        "pos": tree["pos"] * g,
        "rect1": scale_tree(tree["rect1"], g),
        "rect2": scale_tree(tree["rect2"], g),
    }


def min_square_tiling(N, M):
    """縦 n * 横 m の長方形を埋める正方形の最小枚数と復元用の分割ツリーを返す"""

    # 長方形の向きを長辺を横になるように正規化（solve のメモ化が効くように）
    if N < M:
        L, S = M, N
        rotated = True
    else:
        L, S = N, M
        rotated = False

    count, _ = solve(L, S)
    hist = reconstruct(L, S, rotated)
    return count, hist


def collect_rects(rects, history, x=0, y=0):
    w, h = history["size"]
    if history["divide"] == "Self":
        rects.append((x, y, w, h))
    elif history["divide"] == "Long":
        if w > h:
            rects = collect_rects(rects, history["rect1"], x, y)
            rects = collect_rects(rects, history["rect2"], x + history["pos"], y)
        else:
            rects = collect_rects(rects, history["rect1"], x, y)
            rects = collect_rects(rects, history["rect2"], x, y + history["pos"])
    elif history["divide"] == "Short":
        if w > h:
            rects = collect_rects(rects, history["rect1"], x, y)
            rects = collect_rects(rects, history["rect2"], x, y + history["pos"])
        else:
            rects = collect_rects(rects, history["rect1"], x, y)
            rects = collect_rects(rects, history["rect2"], x + history["pos"], y)
    return rects


def draw_tiling(history):
    """分割ツリーをもとに正方形を描画する"""
    width, height = history["size"]
    rects = collect_rects([], history)

    fig_scale = 10  # 画像サイズ
    fig, ax = plt.subplots(
        figsize=((fig_scale * width) / math.sqrt(width * height), (fig_scale * height) / math.sqrt(width * height))
    )
    for rect in rects:
        x, y, w, h = rect
        r = Rectangle(xy=(x, y), width=w, height=h, ec="black", fill=False)
        ax.add_patch(r)
        ax.text(x + w / 2, y + h / 2, w, fontsize = 20 * w * fig_scale / math.sqrt(width * height), horizontalalignment="center", verticalalignment="center")
    
    
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks((0, width))
    ax.set_yticks((0, height))
    fig.tight_layout()
    plt.show()
    fig.savefig(f"./fig/Figure_n={width}_m={height}.png")


if __name__ == "__main__":
    n = int(sys.argv[1])  # 長方形の縦
    m = int(sys.argv[2])  # 長方形の横
    count, history = min_square_tiling(n, m)
    print(f"横{n} × 縦{m} の長方形を埋めるのに必要な正方形の最小数: {count}")
    pprint.pprint(history)
    draw_tiling(history)
