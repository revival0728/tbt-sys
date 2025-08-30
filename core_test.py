from core import *
from utils import compile_player_data, get_match_uuid, PlayerData
import numpy as np

def test_rank_by_knockout():
    tree = [
        ["A", "B", "C", "D"],
        ["B", "D"],
        ["A", "C"],
        ["B"],
        ["D"],
        ["A"],
        ["C"],
    ]
    rank = rank_by_knockout(tree)
    expect_rank = ["C", "A", "D", "B"]
    assert rank == expect_rank

def test_update_knockout_info():
    tree = [
        ["A", "B", "C", "D"],
        [None, None],
        [None, None],
        [None],
        [None],
        [None],
        [None],
    ]
    matches = []

    tree, matches = update_knockout_info(tree, matches, "A")
    expect_tree_1 = [
        ["A", "B", "C", "D"],
        ["B", None],
        ["A", None],
        [None],
        [None],
        [None],
        [None],
    ]
    expect_matches_1 = []
    assert tree == expect_tree_1
    assert matches == expect_matches_1

    tree, matches = update_knockout_info(tree, matches, "C")
    expect_tree_2 = [
        ["A", "B", "C", "D"],
        ["B", "D"],
        ["A", "C"],
        [None],
        [None],
        [None],
        [None],
    ]
    expect_matches_2 = [("B", "D"), ("A", "C")]
    assert tree == expect_tree_2
    assert matches == expect_matches_2
    # C wins
    tree, matches = update_knockout_info(tree, matches, "C")
    expect_tree_3 = [
        ["A", "B", "C", "D"],
        ["B", "D"],
        ["A", "C"],
        [None],
        [None],
        ["A"],
        ["C"],
    ]
    expect_matches_3 = [("B", "D"), ("A", "C")]
    assert tree == expect_tree_3
    assert matches == expect_matches_3
    # D wins
    tree, matches = update_knockout_info(tree, matches, "D")
    expect_tree_4 = [
        ["A", "B", "C", "D"],
        ["B", "D"],
        ["A", "C"],
        ["B"],
        ["D"],
        ["A"],
        ["C"],
    ]
    expect_matches_4 = [("B", "D"), ("A", "C")]
    assert tree == expect_tree_4
    assert matches == expect_matches_4

def test_create_knockout_maches():
    tree = [
        ["A", "B", "C", "D"],
        [None, None],
        [None, None],
        [None],
        [None],
        [None],
        [None],
    ]
    matches = create_knockout_schedules(tree)
    expect_matches = [("A", "B"), ("C", "D")]
    assert matches == expect_matches

def test_create_knockout_tree():
    players = [
        {"nickname": "A"},
        {"nickname": "B"},
        {"nickname": "C"},
        {"nickname": "D"},
    ]
    tree = create_knockout_tree(players, seeding=False)
    expect_tree = [
        ["A", "B", "C", "D"],
        [None, None],
        [None, None],
        [None],
        [None],
        [None],
        [None],
    ]
    assert tree == expect_tree

def test_create_group_matches():
    groups = [
        ["A", "B", "C"],
        ["D", "E", "F", "G"],
    ]
    matches = create_group_schedules(groups)
    expect_matches = [
        ("A", "B"), ("A", "C"), ("B", "C"),
        ("D", "E"), ("D", "F"), ("D", "G"), ("E", "F"), ("E", "G"), ("F", "G"),
    ]
    assert set(matches) == set(expect_matches)

def test_scatter_players_to_groups():
    def test_1():
      players = [
            {"nickname": "A"},
            {"nickname": "B"},
            {"nickname": "C"},
            {"nickname": "D"},
            {"nickname": "E"},
            {"nickname": "F"},
            {"nickname": "G"},
        ]
      groups = scatter_players_to_groups(players, 3)
      assert len(groups) == 3
      for g in groups:
          assert 2 <= len(g) <= 3
      all_players = set()
      for g in groups:
          for p in g:
              all_players.add(p)
      assert all_players == set(p['nickname'] for p in players)
    def test_2():
      players = [
            {"nickname": "A"},
            {"nickname": "B"},
            {"nickname": "C"},
            {"nickname": "D"},
            {"nickname": "E"},
            {"nickname": "F"},
        ]
      groups = scatter_players_to_groups(players, 3)
      assert len(groups) == 3
      for g in groups:
          assert len(g) == 2
      all_players = set()
      for g in groups:
          for p in g:
              all_players.add(p)
      assert all_players == set(p['nickname'] for p in players)
    test_1()
    test_2()

def test_rank_by_group_ideal():
    players = [
        {"nickname": "A"},
        {"nickname": "B"},
        {"nickname": "C"},
        {"nickname": "D"},
        {"nickname": "E"},
        {"nickname": "F"},
        {"nickname": "G"},
    ]
    groups = [
        ["A", "B", "C"],
        ["D", "E", "F", "G"],
    ]

    def gen_match_data() -> list[dict[str, str]]:
      mathces = []
      for g in groups:
        for i in range(len(g)):
          for j in range(i+1, len(g)):
            mathces.append({
              "match_id": get_match_uuid(g[i], g[j]),
              "participant1": g[i],
              "participant2": g[j],
              "first": g[i],
            })
      return mathces
    matches = gen_match_data()

    def gen_game_data() -> list[dict[str, str]]:
      games = []
      for m in matches:
        match_id = m["match_id"]
        p1 = m["participant1"]
        p2 = m["participant2"]
        # p1 win
        games.append({
          "match_id": match_id,
          "score1": 11,
          "score2": 8,
          "winner": 1,
        })
        # p2 win
        games.append({
          "match_id": match_id,
          "score1": 1,
          "score2": 11,
          "winner": 2,
        })
        # p2 win
        games.append({
          "match_id": match_id,
          "score1": 9,
          "score2": 11,
          "winner": 2,
        })
      return games
    games = gen_game_data()

    expect_player_data = PlayerData(
       nickname_id={'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6}, 
       match_res={'2e53beef-af0b-587c-b882-edbc981f435d': [1, 2, 21, 30, 'A', 'B'], 'de43d85d-7dec-5682-b6ae-5c2edafcaf38': [1, 2, 21, 30, 'A', 'C'], '088949c1-9d4f-5491-89f6-d28a0a35004b': [1, 2, 21, 30, 'B', 'C'], 'd188c724-8deb-5611-a13e-819d16288cbb': [1, 2, 21, 30, 'D', 'E'], '4a2626e9-ea5d-55b1-8ab7-62ce298cdb2e': [1, 2, 21, 30, 'D', 'F'], 'ca134c92-8fc9-5ffb-8488-1dc4036f0b4b': [1, 2, 21, 30, 'D', 'G'], '09d1aeb2-a948-584d-abd4-73f3c5ade094': [1, 2, 21, 30, 'E', 'F'], '67700e74-eb3f-5899-83c2-4769ce934765': [1, 2, 21, 30, 'E', 'G'], '7f29461f-246c-5e7c-88db-555478ef35f9': [1, 2, 21, 30, 'F', 'G']}, 
       match_list=[['2e53beef-af0b-587c-b882-edbc981f435d', 'de43d85d-7dec-5682-b6ae-5c2edafcaf38'], ['2e53beef-af0b-587c-b882-edbc981f435d', '088949c1-9d4f-5491-89f6-d28a0a35004b'], ['de43d85d-7dec-5682-b6ae-5c2edafcaf38', '088949c1-9d4f-5491-89f6-d28a0a35004b'], ['d188c724-8deb-5611-a13e-819d16288cbb', '4a2626e9-ea5d-55b1-8ab7-62ce298cdb2e', 'ca134c92-8fc9-5ffb-8488-1dc4036f0b4b'], ['d188c724-8deb-5611-a13e-819d16288cbb', '09d1aeb2-a948-584d-abd4-73f3c5ade094', '67700e74-eb3f-5899-83c2-4769ce934765'], ['4a2626e9-ea5d-55b1-8ab7-62ce298cdb2e', '09d1aeb2-a948-584d-abd4-73f3c5ade094', '7f29461f-246c-5e7c-88db-555478ef35f9'], ['ca134c92-8fc9-5ffb-8488-1dc4036f0b4b', '67700e74-eb3f-5899-83c2-4769ce934765', '7f29461f-246c-5e7c-88db-555478ef35f9']], 
       tw_match=np.array([0, 1, 2, 0, 1, 2, 3], dtype=np.int8), 
       tw_game=np.array([2, 3, 4, 3, 4, 5, 6], dtype=np.int8), 
       tl_game=np.array([4, 3, 2, 6, 5, 4, 3], dtype=np.int8), 
       tw_point=np.array([42, 51, 60, 63, 72, 81, 90], dtype=np.int8),
      tl_point=np.array([60, 51, 42, 90, 81, 72, 63], dtype=np.int8))
    player_data = compile_player_data(players, matches, games)
    assert player_data.nickname_id == expect_player_data.nickname_id
    assert list(player_data.match_res.values()) == list(expect_player_data.match_res.values())
    assert all(len(a) == len(b) and all(len(x) == len(y) for x, y in zip(a, b)) for a, b in zip(player_data.match_list, expect_player_data.match_list))
    assert np.array_equal(player_data.tw_match, expect_player_data.tw_match)
    assert np.array_equal(player_data.tw_game, expect_player_data.tw_game)
    assert np.array_equal(player_data.tl_game, expect_player_data.tl_game)
    assert np.array_equal(player_data.tw_point, expect_player_data.tw_point)
    assert np.array_equal(player_data.tl_point, expect_player_data.tl_point)

    expect_group_rank = [
        ["C", "B", "A"],
        ["G", "F", "E", "D"],
    ]
    expect_final_rank = ["G", "C", "F", "B", "E", "A", "D"]
    group_rank, final_rank = rank_by_group(player_data, groups, [0, 1, 2, 3, 4, 5, 6])
    assert group_rank == expect_group_rank
    assert final_rank == expect_final_rank

def test_rank_by_group_real_data_1():
    players = [
        {"nickname": "A"},
        {"nickname": "B"},
        {"nickname": "C"},
        {"nickname": "D"},
        {"nickname": "E"},
        {"nickname": "F"},
        {"nickname": "G"},
        {"nickname": "H"},
        {"nickname": "I"},
        {"nickname": "J"},
    ]
    groups = [
        ["A", "B", "C", "D"],
        ["E", "F", "G"],
        ["H", "I", "J"],
    ]

    def gen_match_game_data() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
      mathces, games = [], []
      game_result: list[list[list[tuple[int, int, int]]]] = [
        [[(3, 11, 2), (5, 11, 2)], 
         [(4, 11, 2), (5, 11, 2)], 
         [(8, 11, 2), (12, 10, 1), (8, 11, 2)], 
         [(11, 4, 1), (11, 13, 2), (11, 8, 1)], 
         [(11, 5, 1), (11, 8, 1)], 
         [(11, 5, 1), (11, 9, 1)]],
        [[(5, 11, 2), (7, 11, 2)], 
         [(11, 6, 1), (11, 9, 1)], 
         [(11, 4, 1), (11, 6, 1)]],
        [[(11, 6, 1), (11, 5, 1)], 
         [(11, 7, 1), (11, 5, 1)], 
         [(5, 11, 2), (11, 7, 1), (13, 11, 1)]],
      ]
      for gi, g in enumerate(groups):
        game_id = 0
        for i in range(len(g)):
          for j in range(i+1, len(g)):
            match_id = get_match_uuid(g[i], g[j])
            mathces.append({
              "match_id": match_id,
              "participant1": g[i],
              "participant2": g[j],
              "first": g[i],
            })
            for r in game_result[gi][game_id]:
                games.append({
                  "match_id": match_id,
                  "score1": r[0],
                  "score2": r[1],
                  "winner": r[2],
                })
            game_id += 1
      return mathces, games
    matches, games = gen_match_game_data()
    player_data = compile_player_data(players, matches, games)
    expect_group_rank = [
        ["B", "C", "D", "A"],
        ["F", "E", "G"],
        ["H", "I", "J"]
    ]
    expect_final_rank = ["F", "H", "B", "C"]
    group_rank, final_rank = rank_by_group(player_data, groups, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert group_rank == expect_group_rank
    assert final_rank[:4] == expect_final_rank

def test_rank_by_group_real_data_2():
    groups_data = [
        """
1		China	5	5	19	6	42	18
2		Finland	5	3	16	9	35	27
3		HongKong	5	3	15	10	36	29
4		Catalonia	5	3	13	12	30	30
5		Hungary	5	1	8	17	27	37
6		Australia	5	0	4	21	15	44
        """,
        """
1		Poland	5	4	15	10	35	26
2		Italy	5	4	14	11	33	27
3		RCP	5	3	17	8	38	23
4		Germany	5	3	16	9	38	27
5		Uruguay	5	1	7	18	21	41
6		Slovakia	5	0	6	19	20	41
        """,
        """
1		Ukraine	5	4	17	8	39	24
2		Thailand	5	4	16	9	39	27
3		Romania	5	3	12	13	30	34
4		Portugal	5	2	11	14	30	33
5		Mexico	5	1	10	15	27	35
6		Lithuania	5	1	9	16	27	39
        """,
        """
1		Chile	4	3	13	7	30	20
2		Colombia	4	3	11	9	24	24
3		UnitedKingdom	4	2	13	7	30	19
4		Greece	4	2	11	9	27	21
5		Guatemala	4	0	2	18	11	38
        """,
        """
1		UnitedStates	4	4	14	6	30	20
2		Japan	4	3	15	5	31	16
3		CzechRepublic	4	2	10	10	24	25
4		Netherlands	4	1	8	12	26	25
5		Malaysia	4	0	3	17	11	36
        """,
        """
1		Brazil	4	3	13	7	29	19
2		France	4	3	11	9	26	19
3		Argentina	4	2	10	10	24	24
4		Spain	4	1	10	10	21	25
5		Vietnam	4	1	6	14	17	30
        """,
        """
1		Croatia	4	4	15	5	31	21
2		Latvia	4	3	9	11	22	24
3		Taiwan	4	2	10	10	25	22
4		Belgium	4	1	8	12	22	27
5		Tutejšyja	4	0	8	12	22	28
        """,
    ]
    nickname_id = dict()
    match_res = dict()
    match_list = []
    tw_match = []
    tw_game = []
    tl_game = []
    tw_point = []
    tl_point = []
    groups = []
    expect_group_rank = []
    for gdata in groups_data:
        group = []
        for line in gdata.strip().splitlines():
            parts = line.split()
            nickname = parts[1]
            group.append(nickname)
            nickname_id[nickname] = len(nickname_id)
            tw_match.append(int(parts[3]))
            tw_game.append(int(parts[4]))
            tl_game.append(int(parts[5]))
            tw_point.append(int(parts[6]))
            tl_point.append(int(parts[7]))
            match_list.append([])
        for i in range(len(group)):
            for j in range(i+1, len(group)):
                mid = get_match_uuid(group[i], group[j])
                match_res[mid] = [4, 1, 7, 7, group[i], group[j]]
                match_list[nickname_id[group[i]]].append(mid)
                match_list[nickname_id[group[j]]].append(mid)
        expect_group_rank.append(group)
        groups.append(group)
    player_data = PlayerData(
        nickname_id=nickname_id,
        match_res=match_res,
        match_list=match_list,
        tw_match=np.array(tw_match, dtype=np.int8),
        tw_game=np.array(tw_game, dtype=np.int8),
        tl_game=np.array(tl_game, dtype=np.int8),
        tw_point=np.array(tw_point, dtype=np.int8),
        tl_point=np.array(tl_point, dtype=np.int8),
    )
    expect_final_rank = [
        "China",
        "Croatia",
        "UnitedStates",
        "Ukraine",
        "Brazil",
        "Chile",
        "Poland",
        "Japan",
        "Thailand",
        "France",
        "Italy",
        "Columbia",
        "Latvia",
        "Finland",
        "UnitedKingdom",
        "RCP",
        "Taiwan",
        "Hong Kong",
        "Argentina",
        "CzechRepublic",
        "Romania"
    ]
    group_rank, final_rank = rank_by_group(player_data, groups, list(range(len(nickname_id))))
    # print(group_rank)
    # print(final_rank)
    # for twm, twg, tlg, twp, tlp in zip(player_data.tw_match, player_data.tw_game, player_data.tl_game, player_data.tw_point, player_data.tl_point):
    #     print(twm, twg, tlg, twp, tlp)
    assert group_rank == expect_group_rank
    # This one needs more data
    # https://www.carcassonne.cat/wtcoc/results.php?g=1
    # assert final_rank[:len(expect_final_rank)] == expect_final_rank
    assert final_rank[:10] == expect_final_rank[:10]