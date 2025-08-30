import time
import uuid
import socket
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass

NAMESPACE_MATCH = uuid.UUID("a2a3250c-caf5-4729-894f-83f84088978b")

def get_hostm_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_match_uuid(participant1: str, participant2: str) -> str:
    namestr = f"{participant1}:{participant2}:{int(time.time())}"
    return str(uuid.uuid5(NAMESPACE_MATCH, namestr))


@dataclass
class PlayerData:
    nickname_id: dict[str, int]
    match_res: dict[str, list] # {match_id: [p1 win_game, p2 win_game, p1 point, p2 point, p1 nickname, p2 nickname]}

    # [ith_player_dat, ...]
    match_list: list[list[str]]
    tw_match: npt.NDArray[np.int8] # total win match
    tw_game: npt.NDArray[np.int8]  # total win game
    tl_game: npt.NDArray[np.int8]  # total lose game
    tw_point: npt.NDArray[np.int8] # total win point
    tl_point: npt.NDArray[np.int8] # total lose point

def compile_player_data(players: list[dict[str, str]], matches: list[dict[str, str]], games: list[dict[str, str]]) -> PlayerData:
    nickname_id = dict()
    for i, p in enumerate(players):
        nickname_id[p['nickname']] = i
    match_res: dict[str, list] = dict() 
    match_list = [[] for _ in players]
    # tw -> total win, tl -> total lose
    tw_match = np.zeros(len(players), dtype=np.int8)
    tw_game = np.zeros(len(players), dtype=np.int8)
    tl_game = np.zeros(len(players), dtype=np.int8)
    tw_point = np.zeros(len(players), dtype=np.int8)
    tl_point = np.zeros(len(players), dtype=np.int8)
    for g in games:
        match_id = g['match_id']
        score1 = int(g['score1'])
        score2 = int(g['score2'])
        winner = int(g['winner'])
        if score1 < score2:
            score1, score2 = score2, score1
        if match_id not in match_res:
            match_res[match_id] = [0, 0, 0, 0] # p1 win_game, p2 win_game, p1 point, p2 point
        if winner == 1:
            match_res[match_id][0] += 1
            match_res[match_id][2] += score1
            match_res[match_id][3] += score2
        elif winner == 2:
            match_res[match_id][1] += 1
            match_res[match_id][2] += score2
            match_res[match_id][3] += score1
        else:
            raise ValueError(f"Invalid winner value: {winner}")
    for m in matches:
        match_id = m['match_id']
        p1 = m['participant1']
        p2 = m['participant2']
        match_res[match_id].append(p1)
        match_res[match_id].append(p2)
        match_list[nickname_id[p1]].append(match_id)
        match_list[nickname_id[p2]].append(match_id)
        if match_id not in match_res:
            raise ValueError(f"Match ID {match_id} in matches not found in games")
        res = match_res[match_id]
        id1 = nickname_id[p1]
        id2 = nickname_id[p2]
        if res[0] > res[1]:
            tw_match[id1] += 1
        else:
            tw_match[id2] += 1
        tw_game[id1] += res[0]
        tw_game[id2] += res[1]
        tl_game[id1] += res[1]
        tl_game[id2] += res[0]
        tw_point[id1] += res[2]
        tw_point[id2] += res[3]
        tl_point[id1] += res[3]
        tl_point[id2] += res[2]
    return PlayerData(nickname_id, match_res, match_list, tw_match, tw_game, tl_game, tw_point, tl_point)