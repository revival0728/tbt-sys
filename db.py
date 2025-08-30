import os
import json
import multiprocessing as mtpr
import tbt_config
from typing import Any, Protocol

# for debug
import server
def app_logger_debug(msg: str):
    with server.app.app_context():
        server.app.logger.debug(msg)

class TransactFunc(Protocol):
    def __call__(self, *datas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]: ...
class DeclineTransaction(Exception):
    pass

class DB:
    def __init__(self):
        self.store_dir = "data"
        self.lock = mtpr.Lock()
        if os.path.isdir(self.store_dir) is False:
            os.mkdir(self.store_dir)
        self.buckets = set(["players", "matches", "games", "game_in_progress", "schedules", "ranking"])
        if tbt_config.COMPETITION_FORMAT == "group":
            self.buckets.add("groups")
        if tbt_config.COMPETITION_FORMAT == "knockout":
            self.buckets.add("kntree")
    def __save_raw(self, bucket: str, data: dict):
        if not bucket in self.buckets:
            raise ValueError(f"Unknown bucket: {bucket}")
        with open(os.path.join(self.store_dir, f"{bucket}.txt"), "a") as f:
            f.write(json.dumps(data) + "\n")
    def __load_raw(self, bucket: str, load_last=True) -> list[dict[str, Any]]:
        if not bucket in self.buckets:
            raise ValueError(f"Unknown bucket: {bucket}")
        if os.path.isfile(os.path.join(self.store_dir, f"{bucket}.txt")) is False:
            if load_last:
                return [{}]
            return []
        with open(os.path.join(self.store_dir, f"{bucket}.txt"), "r") as f:
            lines = f.readlines()
        if load_last:
            if len(lines) == 0:
                return [{}]
            return [json.loads(lines[-1])]
        return [json.loads(line) for line in lines]
    def save(self, bucket: str, data: dict):
        with self.lock:
            self.__save_raw(bucket, data)
    def load(self, bucket: str, load_last=False) -> list[dict[str, Any]]:
        with self.lock:
            return self.__load_raw(bucket, load_last)
    def transact(self, buckets: list[str], func: TransactFunc, load_last_list: list[bool] | None=None) -> Any:
        if load_last_list is None:
            load_last_list = [False for _ in buckets]
            assert len(load_last_list) == len(buckets)
        with self.lock:
            try:
                datas = []
                for bucket, load_last in zip(buckets, load_last_list):
                    if not bucket in self.buckets:
                        raise ValueError(f"Unknown bucket: {bucket}")
                    datas.append(self.__load_raw(bucket, load_last))
                new_datas = func(*datas)
                for bucket in new_datas:
                    self.__save_raw(bucket, new_datas[bucket])
            except DeclineTransaction as dt:
                return dt.args[0] if len(dt.args) > 0 else None
    def is_empty_unchecked(self, bucket: str) -> bool:
        if os.path.isfile(os.path.join(self.store_dir, f"{bucket}.txt")) is False:
            return True
        with open(os.path.join(self.store_dir, f"{bucket}.txt"), "r") as f:
            lines = f.readlines()
        return len("".join(lines).strip()) == 0
    def is_empty(self, bucket: str):
        with self.lock:
            if not bucket in self.buckets:
                raise ValueError(f"Unknown bucket: {bucket}")
            return self.is_empty_unchecked(bucket)
    def clear_unchecked(self, bucket: str):
        if os.path.isfile(os.path.join(self.store_dir, f"{bucket}.txt")) is True:
            os.remove(os.path.join(self.store_dir, f"{bucket}.txt"))
    def clear(self, bucket: str):
        with self.lock:
            if not bucket in self.buckets:
                raise ValueError(f"Unknown bucket: {bucket}")
            self.clear_unchecked(bucket)