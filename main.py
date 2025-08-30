from qrcode.image.pure import PyPNGImage
import multiprocessing as mtpr
import waitress
import server
import core
import tbt_config
import qrcode
import os
import utils

HOST_FULL_IP = None

def start_server():
    waitress.serve(server.app, host='0.0.0.0', port=tbt_config.SERVER_PORT)

def make_webpage_qrcode():
    if os.path.isdir("qrcodes") is False:
        os.mkdir("qrcodes")
    def save_qr_code(page: str):
        assert HOST_FULL_IP is not None
        url = f"{HOST_FULL_IP}{page}"
        img = qrcode.make(url, image_factory=PyPNGImage)
        with open(os.path.join("qrcodes", f"{page}.png"), "wb") as f:
            img.save(f)
    for page in server.QR_CODE_PAGE:
        save_qr_code(page)

def check_existing_competition():
    with server.app.app_context():
        db = server.get_db()
        groups_empty = db.is_empty_unchecked('groups')
        kntree_empty = db.is_empty_unchecked('kntree')
        schedules_empty = db.is_empty_unchecked('schedules')
        if tbt_config.COMPETITION_FORMAT == "group" and not kntree_empty:
            raise ValueError("資料庫中存在淘汰賽的資料，請手動清除 data/ 目錄後重新開始比賽")
        if tbt_config.COMPETITION_FORMAT == "knockout" and not groups_empty:
            raise ValueError("資料庫中存在循環賽的資料，請手動清除 data/ 目錄後重新開始比賽")
        if not kntree_empty and not groups_empty:
            raise ValueError("資料庫中同時存在循環賽與淘汰賽的資料，請手動清除 data/ 目錄後重新開始比賽")
        if tbt_config.COMPETITION_FORMAT == "group" and groups_empty and schedules_empty:
            return False
        if tbt_config.COMPETITION_FORMAT == "group" and not groups_empty and not schedules_empty:
            return True
        if tbt_config.COMPETITION_FORMAT == "knockout" and  kntree_empty and schedules_empty:
            return False
        if tbt_config.COMPETITION_FORMAT == "knockout" and not kntree_empty and not schedules_empty:
            return True
        raise ValueError("資料庫中存在不完整的比賽資料，請手動清除 data/ 目錄後重新開始比賽")

def init_competition():
    with server.app.app_context():
        db = server.get_db()
        if tbt_config.COMPETITION_FORMAT == "group":
            players = db.load('players')
            if len(players) == 0:
                raise ValueError("沒有選手，無法開始比賽")
            groups = core.scatter_players_to_groups(players, tbt_config.GROUP_COUNT)
            db.save('groups', {'groups': groups})
            matches = core.create_group_schedules(groups)
            schedule = [(p1, p2) for p1, p2 in matches]
            db.save('schedules', {'matches': schedule})
        elif tbt_config.COMPETITION_FORMAT == "knockout":
            players = db.load('players')
            if len(players) != 4:
                raise ValueError("單淘汰賽目前僅支援 4 人參賽")
            if tbt_config.KNOCKOUT_SEEDING not in ["random", "ordered"]:
                raise ValueError("單淘汰賽的種子排列方式只能是 'random' 或 'ordered'")
            seeding = tbt_config.KNOCKOUT_SEEDING == "random"
            kntree = core.create_knockout_tree(players, seeding)
            db.save('kntree', {'tree': kntree})
            matches = core.create_knockout_schedules(kntree)
            db.save('schedules', {'matches': matches})
        else:
            raise ValueError("未知的比賽賽制，請確認 tbt_config.COMPETITION_FORMAT")

def expect_input(prompt: str, valid_input: str | list[str]) -> int | None:
    while True:
        user_input = input(prompt).strip().lower()
        if type(valid_input) == str and user_input == valid_input:
            return
        if type(valid_input) == list and user_input in valid_input:
            return valid_input.index(user_input)

def main():
    try:
        global HOST_FULL_IP
        mtpr.set_start_method('fork')
        if tbt_config.SERVER_PORT is None:
            tbt_config.SERVER_PORT = 8080
        HOST_FULL_IP = f"http://{utils.get_hostm_ip()}:{tbt_config.SERVER_PORT}/"
        server_process = mtpr.Process(target=start_server)
        server_process.start()
        print(f"Server running at {HOST_FULL_IP}")

        def start_new_competition():
            print("請確認比賽規則無誤，輸入 'confirm' 確認")
            print("*" * 20)
            if tbt_config.COMPETITION_FORMAT == "group":
                print(f"比賽賽制為小組循環賽，總共分為 {tbt_config.GROUP_COUNT} 組。")
            elif tbt_config.COMPETITION_FORMAT == "knockout":
                print(f"比賽賽制為單淘汰賽，種子排列方式為 {tbt_config.KNOCKOUT_SEEDING}。")
            print(f"每場比賽採用 {tbt_config.GAMES_PER_MATH} 局 {tbt_config.GAMES_PER_MATH // 2 + 1} 勝制。")
            print(f"每局比賽採用 {tbt_config.WINNING_SCORE} 分制。")
            print("*" * 20)
            expect_input("> ", "confirm")
            print("比賽規則確認無誤，正在初始化比賽資料...")
            init_competition()
            print("正在產生網頁 QR Code...")
            make_webpage_qrcode()
            print("比賽開始！")

        def quit_competition():
            print("輸入 'quit' 結束比賽並關閉伺服器")
            expect_input("> ", "quit")
            print("比賽結束，正在關閉伺服器...")
            server_process.terminate()

        print("輸入 'start' 開始比賽")
        print("請注意，開始比賽後，無法再新增選手！")
        print("請確保所有選手都已註冊完成，並且比賽規則已設定完成。")
        expect_input("> ", "start")
        if check_existing_competition():
            print("偵測到已有進行中的比賽資料，請確認是否要繼續使用這些資料？")
            print("輸入 'confirm' 繼續使用現有資料，輸入 'new' 清除所有資料並開始新的比賽：")
            recieve = expect_input("> ", ["confirm", "new"])
            if recieve == 1:
                print("正在清除現有比賽資料...")
                with server.app.app_context():
                    db = server.get_db()
                    db.clear_unchecked('matches')
                    db.clear_unchecked('games')
                    db.clear_unchecked('game_in_progress')
                    db.clear_unchecked('schedules')
                    db.clear_unchecked('groups')
                    db.clear_unchecked('kntree')
                    db.clear_unchecked('ranking')
                print("現有比賽資料已清除")
                start_new_competition()
                quit_competition()
                return
            else:
                print("繼續使用現有比賽資料")
            quit_competition()
            return
        start_new_competition()
        quit_competition()
        return
    except ValueError as ve:
        print(f"錯誤：{ve}")
        print("比賽無法開始，正在關閉伺服器...")
        server_process.terminate()
    except KeyboardInterrupt:
        print("比賽結束，正在關閉伺服器...")
        server_process.terminate()

if __name__ == "__main__":
    main()