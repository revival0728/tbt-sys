import time
import os
import shutil

BACKUP_DIR = os.path.join('data', str(int(time.time())))

def backup(bucket: str):
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    bucket_file = f"{bucket}.txt"
    if not os.path.isfile(os.path.join('data', bucket_file)):
        print(f"資料夾中沒有 {bucket}，跳過備份")
        return
    shutil.copy(os.path.join('data', bucket_file), os.path.join(BACKUP_DIR, bucket_file))
    print(f"已備份 {bucket} 至 {BACKUP_DIR}")

for bucket in ["players", "matches", "games", "game_in_progress", "schedules", "ranking", "groups", "kntree"]:
    backup(bucket)