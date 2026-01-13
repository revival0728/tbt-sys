import flask
from flask import Flask, request
from db import DB, DeclineTransaction
from utils import get_match_uuid
import tbt_config
import uuid
import typing
import core
import utils

#FIXME: game_scoring.html 在手機上面會超出螢幕
#FIXME: game_scoring.html 局數偶數時，發球顯示錯誤。 (應該是 JS 的問題)
#TODO: set knockout to imcomplete

QR_CODE_PAGE = ['ranking', 'new_match', 'register', 'groups', 'schedules']

app = Flask(__name__)

def get_db() -> DB:
    if not hasattr(flask.g, 'db'):
        flask.g.db = DB()
    return flask.g.db

def render_template(template_name: str, **context: typing.Any):
    return flask.render_template(template_name, 
                                 competition_title=tbt_config.COMPETITION_TITLE,
                                 **context)

@app.route('/schedules')
def schedules():
    db = get_db()
    schedules = db.load('schedules', load_last=True)[0].get('matches', [])
    return render_template('schedules.html', schedules=schedules)

@app.route('/groups')
def groups():
    if tbt_config.COMPETITION_FORMAT != "group":
        return "目前賽制不是循環賽"
    db = get_db()
    groups = db.load('groups', load_last=True)[0].get('groups', [])
    return render_template('groups.html', groups=groups)

@app.route('/ranking')
def ranking():
    db = get_db()
    is_ranking_empty = db.is_empty('ranking')
    if not is_ranking_empty:
        ranking = db.load('ranking', load_last=True)[0].get('ranking', [])
        return render_template('ranking.html', ranking=ranking)
    competition_over = False
    if tbt_config.COMPETITION_FORMAT == "knockout":
        kntree = db.load('kntree', load_last=True)[0]
        tree = kntree.get('tree', [])
        if all(node is not None for node in tree):
            competition_over = True
    if tbt_config.COMPETITION_FORMAT == "group":
        schedules = db.load('schedules', load_last=True)[0]
        if len(schedules.get('matches', [])) == 0:
            competition_over = True
    player_data = None
    if competition_over and is_ranking_empty:
        ranking = None
        players = db.load('players')
        matches = db.load('matches')
        games = db.load('games')
        player_data = utils.compile_player_data(players, matches, games)
        if tbt_config.COMPETITION_FORMAT == "group":
            groups = db.load('groups', load_last=True)[0].get('groups', {})
            ranking = core.rank_by_group(player_data, groups)[1]
        if tbt_config.COMPETITION_FORMAT == "knockout":
            kntree = db.load('kntree', load_last=True)[0]
            ranking = core.rank_by_knockout(kntree.get('tree', []))
        compiled_ranking = []
        assert ranking is not None
        for r in ranking:
            pid = player_data.nickname_id[r]
            compiled_ranking.append({
                'nickname': r,
                'tw_match': int(player_data.tw_match[pid]),
                'tw_game': int(player_data.tw_game[pid]),
                'tl_game': int(player_data.tl_game[pid]),
                'tw_point': int(player_data.tw_point[pid]),
                'tl_point': int(player_data.tl_point[pid]),
            })
        db.save('ranking', {'ranking': compiled_ranking})
    if competition_over:
        return render_template('ranking.html', ranking=ranking)
    return render_template('ranking.html', ranking=None)

@app.route('/game_scoring/<uuid:match_id_uuid>', methods=['GET', 'POST'])
def game_scoring(match_id_uuid: uuid.UUID):
    match_id = str(match_id_uuid)
    db = get_db()
    if request.method == 'POST':
        score1 = int(request.form['score1'])
        score2 = int(request.form['score2'])
        winner = int(request.form['winner'])
        matches = db.load('matches')
        match_info = next((m for m in matches if m['match_id'] == match_id), dict())
        match_over = False
        def t_gip(*datas: list[dict[str, typing.Any]]) -> dict[str, dict[str, typing.Any]]:
            nonlocal match_over
            gip = datas[0][0]
            games = datas[1]
            if gip.get(match_id) is None:
                raise DeclineTransaction("ERROR: 這個比賽組合不存在")
            if score1 < 0 or score2 < 0 or (score1 < tbt_config.WINNING_SCORE and score2 < tbt_config.WINNING_SCORE):
                raise DeclineTransaction(f"ERROR: 分數必須是非負數，且至少有一方達到 {tbt_config.WINNING_SCORE} 分")
            if abs(score1 - score2) < 2:
                raise DeclineTransaction("ERROR: 必須領先對手至少兩分")
            games.append({
                'match_id': match_id,
                'score1': score1,
                'score2': score2,
                'winner': winner
            })
            gip[match_id] += 1
            game_results = filter(lambda g: g['match_id'] == match_id, games)
            game_wins = [0, 0]
            for result in game_results:
                game_wins[result['winner'] - 1] += 1
            if game_wins[0] == (tbt_config.GAMES_PER_MATH // 2) + 1 or game_wins[1] == (tbt_config.GAMES_PER_MATH // 2) + 1:
                match_over = True
                del gip[match_id]
            return {
                'game_in_progress': gip,
                'games': {
                    'match_id': match_id,
                    'score1': score1,
                    'score2': score2,
                    'winner': winner
                }
            }
        def t_schedules_kntree(*datas: list[dict[str, typing.Any]]) -> dict[str, dict[str, typing.Any]]:
            kntree = datas[0][0]
            schedules = datas[1][0]
            winner_nn = match_info['participant1'] if winner == 1 else match_info['participant2']
            new_kntree, new_schedules = core.update_knockout_info(kntree.get('tree', []), schedules.get('matches', []), winner_nn)
            return {
                'kntree': {'tree': new_kntree},
                'schedules': {'matches': new_schedules}
            }
        res = db.transact(['game_in_progress', 'games'], t_gip, load_last_list=[True, False])
        if match_over and tbt_config.COMPETITION_FORMAT == "knockout":
            db.transact(['kntree', 'schedules'], t_schedules_kntree, load_last_list=[True, True])
        if res is not None:
            return res
        if match_over:
            return render_template('game_result.html', score1=score1, score2=score2)
        return render_template('game_result.html', score1=score1, score2=score2, match_id=match_id)
    else:
        gip = db.load('game_in_progress', load_last=True)[0]
        game_round = gip.get(match_id)
        if game_round is None:
            return "ERROR: 這個比賽組合不存在"
        if game_round >= tbt_config.GAMES_PER_MATH + 1:
            return "ERROR: 這個比賽已經結束"
        game_info_list = db.load('matches')
        game_info = next((g for g in game_info_list if g['match_id'] == match_id), None)
        if game_info is None:
            return "ERROR: 找不到比賽資訊"
        return render_template('game_scoring.html', 
                               match_id=match_id, 
                               game_info=game_info, 
                               game_round=game_round,
                               games_per_match=tbt_config.GAMES_PER_MATH,
                               winning_score=tbt_config.WINNING_SCORE)

@app.route('/new_match', methods=['GET', 'POST'])
def new_match():
    db = get_db()
    if request.method == 'POST':
        participant1 = request.form['participant1']
        participant2 = request.form['participant2']
        first = request.form['first']
        match_id = get_match_uuid(participant1, participant2)
        def t_schedules_gip(*datas: list[dict[str, typing.Any]]) -> dict[str, dict[str, typing.Any]]:
            schedules = datas[0][0]
            gip = datas[1][0]
            expected_matches = schedules.get('matches', [])
            if [participant1, participant2] not in expected_matches and [participant2, participant1] not in expected_matches:
                raise DeclineTransaction("ERROR: 這個組合不在賽程中")
            app.logger.debug(f"New game request: {request.form}")
            if participant1 == participant2:
                raise DeclineTransaction("ERROR: 不能與自己發起比賽比賽😃")
            if gip.get(match_id) is not None:
                raise DeclineTransaction("ERROR: 這個組合正在進行比賽")
            gip[match_id] = 1
            if [participant1, participant2] in expected_matches:
                schedules['matches'].remove([participant1, participant2])
            else:
                schedules['matches'].remove([participant2, participant1])
            return {
                'schedules': schedules,
                'game_in_progress': gip,
                'matches': {
                    'match_id': match_id,
                    'participant1': participant1,
                    'participant2': participant2,
                    'first': first
                }
            }
        res = db.transact(['schedules', 'game_in_progress'], t_schedules_gip, load_last_list=[True, True])
        if res is not None:
            return res
        return render_template('new_match_result.html',
                               participant1=participant1,
                               participant2=participant2,
                               first=first,
                               match_id=match_id)
    else:
        players = db.load('players')
        return render_template('new_match.html', players=players)

@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    if request.method == 'POST':
        nickname = request.form['nickname']
        def t_players(*datas: list[dict[str, str]]) -> dict[str, dict[str, str]]:
            players = datas[0]
            if any(p['nickname'] == nickname for p in players):
                raise DeclineTransaction("這個暱稱已經被註冊過了")
            return {
                'players': {'nickname': nickname}
            }
        res = db.transact(['players'], t_players)
        if res is not None:
            return res
        return render_template('register_result.html', message="註冊成功: " + nickname)
    else:
        return render_template('register.html')

@app.route('/')
def homepage():
    return "Welcome to the tbt-sys homepage!"

def main():
    print("Hello from tbt-sys!")

if __name__ == "__main__":
    main()
