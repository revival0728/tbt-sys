import numpy as np
import numpy.typing as npt
from utils import PlayerData

def rank_by_knockout(tree: list[list[str]]) -> list[str]:
    assert all(p is not None for p in tree[1])
    assert all(p is not None for p in tree[2])
    return [tree[i][0] for i in range(-1, -5, -1)]

def update_knockout_info(tree: list[list[str]], schedules: list[tuple[str, str]], winner: str) -> tuple[list[list[str]], list[tuple[str, str]]]:
    assert winner in tree[0]
    max_level = -1
    for i, subt in enumerate(tree[:3]):
        if winner in subt:
            max_level = i
    assert max_level != -1, "Winner not found in the first three levels of the tree"
    idx = tree[max_level].index(winner)
    if max_level == 0:
        tree[2][idx // 2] = winner
        tree[1][idx // 2] = tree[0][idx ^ 1]
    if max_level >= 1:
        tree[max_level * 2 + 2][idx // 2] = winner
        tree[max_level * 2 + 1][idx // 2] = tree[max_level][idx ^ 1]
    for subt in tree[1:3]:
        if None not in subt and max_level == 0:
            schedules.append((subt[0], subt[1]))
    return tree, schedules

def create_knockout_schedules(tree: list[list[str]]) -> list[tuple[str, str]]:
    assert len(tree[0]) == 4
    schedules = []
    for i in range(0, len(tree[0]), 2):
        schedules.append((tree[0][i], tree[0][i + 1]))
    return schedules

def create_knockout_tree(players: list[dict[str, str]], seeding: bool, seed: int | None = None) -> list[list[str]]:
    player_count = len(players)
    assert player_count == 4
    first_stage = [p['nickname'] for p in players]
    if seeding:
        rng = np.random.default_rng(seed)
        rng.shuffle(first_stage)
    tree = [first_stage, [None, None], [None, None], [None], [None], [None], [None]]
    return tree

def create_group_schedules(groups: list[list[str]]) -> list[tuple[str, str]]:
    schedules = []
    for g in groups:
        n = len(g)
        for i in range(n):
            for j in range(i+1, n):
                schedules.append((g[i], g[j]))
    return schedules

def scatter_players_to_groups(players: list[dict[str, str]], group_count: int, seed: int | None = None) -> list[list[str]]:
    id_to_nickname = [p['nickname'] for p in players]
    player_count = len(players)
    indices = np.arange(player_count)
    rng = np.random.default_rng(seed)
    rng.shuffle(indices)
    group_id = np.mod(indices, group_count)
    groups: list[list[str]] = [[] for _ in range(group_count)]
    for i, gi in enumerate(group_id):
        groups[gi].append(id_to_nickname[i])
    return groups

def rank_by_group(player_data: PlayerData, groups: list[list[str]], draw_comp: None | list[int | float] | npt.ArrayLike = None) -> tuple[list[list[str]], list[str]]:
    """
    * 小組排名計算：
        1. 以勝場高低決定排名。
        2. 若兩方勝場相同，比較雙方對戰結果，勝者排名較高。
        3. 若三方(含)以上積分相同，比較彼此對戰結果：
        (a)（總勝局數）÷（總負局數）較大者排名較高。
        (b)（總勝分）÷（總負分）較大者排名較高。
        (c) 若仍相同，則由抽籤決定。
    * 總排名計算(不計與最多人組別的最後一名的對戰結果):
        1. 小組排名。
        2. 總勝場數。
        3. 總勝局數 ÷ 總負局數。
        4. 總勝分 ÷ 總負分。
        5. 若仍相同，則由抽籤決定。
    """
    nickname_id = player_data.nickname_id
    match_res = player_data.match_res
    match_list = player_data.match_list
    tw_match = player_data.tw_match
    tw_game = player_data.tw_game
    tl_game = player_data.tl_game
    tw_point = player_data.tw_point
    tl_point = player_data.tl_point
    player_count = len(nickname_id)
    if draw_comp is None:
        draw_comp = np.random.default_rng().random(player_count) # good luck
    elif isinstance(draw_comp, list):
        assert len(draw_comp) == player_count
        draw_comp = np.array(draw_comp)
    elif not isinstance(draw_comp, np.ndarray):
        raise ValueError("draw_comp must be None, list[int | float], or numpy.ArrayLike")
    else:
        raise ValueError("draw_comp must be None, list[int | float], or numpy.ArrayLike")
    
    # calculate group rank
    def rank_if_tw_match_same(id: npt.NDArray[np.intp]) -> npt.NDArray[np.intp]:
        if len(id) == 1:
            return id
        if len(id) == 2:
            p1m_list = set(match_list[id[0]])
            p2m_list = set(match_list[id[1]])
            matches: set[str] = p1m_list.intersection(p2m_list)
            assert len(matches) == 1, f"Error: 兩人之間應該只有一場比賽，但找到 {len(matches)} 場"
            match_id = matches.pop()
            res = match_res[match_id]
            p1w = res[0] if nickname_id[res[4]] == id[0] else res[1]
            p2w = res[1] if nickname_id[res[5]] == id[1] else res[0]
            # higer index -> higher rank
            if p1w > p2w:
                return id[::-1]
            else:
                return id
        return id[np.lexsort([draw_comp[id], tw_point[id]/tl_point[id], tw_game[id]/tl_game[id]])]
    def rank_tw_match(id: npt.NDArray[np.intp]) -> npt.NDArray[np.intp]:
        return id[np.lexsort([tw_match[id]])]
    def rank_group(id: npt.NDArray[np.intp]) -> list[int]:
        rank = rank_tw_match(id)
        rank = [rank_if_tw_match_same(rank[tw_match[rank] == r]) for r in np.unique(tw_match[rank])]
        return [int(i) for r in rank[::-1] for i in r[::-1]] # lower index -> higher rank

    group_rank = [rank_group(np.array([nickname_id[n] for n in g])) for g in groups]

    def remove_last_rank_effect() -> npt.NDArray[np.intp]:
        group_sizes = [len(g) for g in group_rank]
        max_size = max(group_sizes)
        ret = np.ones(player_count, dtype=np.intp) # no one is removed
        if all(s == max_size for s in group_sizes):
            return ret
        remove_id = -1
        for gp in group_rank:
            if len(gp) < max_size:
                continue
            remove_id = gp[-1]
            ret[remove_id] = 0 # removed
            for mr in match_res:
                [p1w, p2w, p1p, p2p, p1n, p2n] = match_res[mr]
                if nickname_id[p1n] == remove_id or nickname_id[p2n] == remove_id:
                    if nickname_id[p2n] == remove_id:
                        p1w, p2w = p2w, p1w
                        p1p, p2p = p2p, p1p
                        p1n, p2n = p2n, p1n
                    if p1w < p2w:
                        tw_match[nickname_id[p2n]] -= 1
                    tw_game[nickname_id[p2n]] -= p2w
                    tl_game[nickname_id[p2n]] -= p1w
                    tw_point[nickname_id[p2n]] -= p2p
                    tl_point[nickname_id[p2n]] -= p1p
        return ret
        

    unfair_comp = remove_last_rank_effect()

    # calculate final rank
    def rank_final(id: npt.NDArray[np.intp]) -> list[int]:
        group_rank_flat = np.zeros(len(id), dtype=np.intp) # larger value -> higher rank
        for g in group_rank:
            for r, i in enumerate(g):
                group_rank_flat[i] = -r
        return id[np.lexsort(
            [draw_comp[id], tw_point[id]/tl_point[id], tw_game[id]/tl_game[id], tw_match[id], group_rank_flat[id], unfair_comp[id]]
            )][::-1].tolist() # lower index -> higher rank
    
    final_rank = rank_final(np.arange(player_count))

    id_to_nickname = [p for p in sorted(nickname_id.keys(), key=lambda x: nickname_id[x])]

    return [[id_to_nickname[i] for i in g] for g in group_rank], [id_to_nickname[i] for i in final_rank]