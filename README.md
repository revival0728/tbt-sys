# TBT-SYS 桌球比賽管理系統

一個功能完整的桌球比賽管理系統，支援選手註冊、比賽排程、即時計分、排名統計等功能。系統採用 Flask 框架開發，支援分組賽和淘汰賽兩種比賽格式。

## 🏆 功能特色

- **選手註冊管理**：簡潔的選手註冊介面
- **智慧比賽排程**：自動生成分組賽或淘汰賽賽程
- **即時計分系統**：專業的桌球計分板，支援換場和發球規則
- **自動排名統計**：根據官方桌球規則自動計算排名
- **美觀的用戶介面**：現代化設計，支援響應式佈局
- **多程序安全**：使用文件鎖確保數據一致性
- **自動生成QRCode**：無需發網址給參賽者，列印或顯示QRCode即可讓參賽者使用

## 📁 項目結構

```
tbt-sys/
├── core.py              # 核心比賽邏輯
├── server.py            # Flask Web 服務器
├── db.py                # 數據庫管理
├── utils.py             # 工具函數
├── main.py              # 主程序入口
├── tbt_config.py        # 配置文件
├── data/                # 數據存儲目錄（由程式生成）
├── templates/           # HTML 模板
└── qrcodes/             # 網址 QR Code 圖片（由程式生成）
```

## 🚀 快速開始

1. **安裝依賴**
```bash
uv sync
uv sync --all-groups  #開發者需安專開發依賴
```

2. **配置系統**
編輯 `tbt_config.py` 設定比賽參數：
```python
COMPETITION_TITLE = "你的筆賽名稱"

GAMES_PER_MATH = 3

WINNING_SCORE = 11

# "group" or "knockout"
COMPETITION_FORMAT = "knockout"

# 只需在循環賽模式設定
GROUP_COUNT = 2

# 只需在淘汰賽模式設定
# "random" or "ordered"
KNOCKOUT_SEEDING = "random" 

# 如果為 None 預設為 8080
SERVER_PORT = None
```

3. **啟動服務器**
```bash
python3 main.py
```

4. **訪問系統**

打開瀏覽器訪問終端機輸出的網址

## ⚠️ 注意

- 淘汰賽目前只支援4人
- 目前尚未大量測試系統穩定度

---

## 📖 模組詳細說明

### 🧠 core.py - 核心比賽邏輯

處理分組賽和淘汰賽的核心算法，包括排程生成、排名計算等功能。

#### 分組賽相關函數

##### `scatter_players_to_groups(players, group_count, seed=None)`
將選手分配到各個小組
- **參數**：
  - `players`: 選手列表 `[{'nickname': str}, ...]`
  - `group_count`: 小組數量
  - `seed`: 隨機種子（可選）
- **返回**：`list[list[str]]` - 各小組的選手名單

##### `create_group_schedules(groups)`
為分組賽生成完整的比賽排程
- **參數**：
  - `groups`: 小組列表 `list[list[str]]`
- **返回**：`list[tuple[str, str]]` - 比賽對戰組合

##### `rank_by_group(player_data, groups, draw_comp=None)`
根據官方桌球規則計算分組賽排名
- **排名規則**：
  * 小組排名計算：
    1. 以勝場高低決定排名。
    2. 若兩方勝場相同，比較雙方對戰結果，勝者排名較高。
    4. （總勝局數）÷（總負局數）較大者排名較高。
    5. （總勝分）÷（總負分）較大者排名較高。
    6. 若仍相同，則由抽籤決定。
  * 總排名計算(不計與最多人組別的最後一名的對戰結果):
    1. 小組排名。
    2. 總勝場數。
    3. 總勝局數 ÷ 總負局數。
    4. 總勝分 ÷ 總負分。
    5. 若仍相同，則由抽籤決定。
- **參數**：
  - `player_data`: PlayerData 對象
  - `groups`: 小組分配
  - `draw_comp`: 抽籤比較值（可選）
- **返回**：`tuple[list[list[str]], list[str]]` - (小組排名, 總排名)

#### 淘汰賽相關函數

##### `create_knockout_tree(players, seeding, seed=None)`
創建淘汰賽對戰樹
- **參數**：
  - `players`: 選手列表（必須4人）
  - `seeding`: 是否隨機排種
  - `seed`: 隨機種子（可選）
- **返回**：`list[list[str]]` - 對戰樹結構

##### `create_knockout_schedules(tree)`
生成淘汰賽首輪賽程
- **參數**：
  - `tree`: 對戰樹
- **返回**：`list[tuple[str, str]]` - 首輪對戰組合

##### `update_knockout_info(tree, schedules, winner)`
更新淘汰賽進度
- **參數**：
  - `tree`: 當前對戰樹
  - `schedules`: 待進行賽程
  - `winner`: 獲勝者名稱
- **返回**：`tuple[list[list[str]], list[tuple[str, str]]]` - (更新後對戰樹, 新賽程)

##### `rank_by_knockout(tree)`
計算淘汰賽最終排名
- **參數**：
  - `tree`: 完整的對戰樹
- **返回**：`list[str]` - 按排名順序的選手列表

---

### 🌐 server.py - Flask Web 服務器

提供 Web 介面和 API 端點，處理用戶請求和業務邏輯。

#### 路由功能說明

##### `GET/POST /register`
**選手註冊**
- **GET**: 顯示註冊表單
- **POST**: 處理註冊請求
  - 表單字段：`nickname` (暱稱)
  - 驗證：檢查暱稱是否重複
  - 成功：返回註冊成功頁面
  - 失敗：返回錯誤訊息

##### `GET/POST /new_match`
**新建比賽**
- **GET**: 顯示比賽創建表單（包含所有已註冊選手）
- **POST**: 處理比賽創建請求
  - 表單字段：
    - `participant1`: 參賽者1
    - `participant2`: 參賽者2  
    - `first`: 首發球員
  - 驗證：
    - 檢查組合是否在賽程中
    - 防止重複比賽
    - 防止自己與自己比賽
  - 成功：跳轉到比賽確認頁面

##### `GET/POST /game_scoring/<uuid:match_id_uuid>`
**比賽計分**
- **GET**: 顯示計分板介面
  - 包含比賽資訊、當前局數、計分規則
- **POST**: 處理分數提交
  - 表單字段：
    - `score1`: 選手1分數
    - `score2`: 選手2分數
    - `winner`: 獲勝者 (1或2)
  - 驗證：
    - 分數非負且至少一方達到獲勝分數
    - 必須領先至少2分
  - 功能：
    - 自動判斷比賽是否結束
    - 淘汰賽模式下自動更新對戰樹
    - 返回結果頁面

##### `GET /ranking`
**排名查看**
- 智能顯示邏輯：
  - 比賽進行中：顯示空排名
  - 比賽結束：自動計算並顯示最終排名
  - 包含詳細統計：勝場數、勝負局數、勝負分數

#### 輔助函數

##### `get_db()`
獲取數據庫實例，使用 Flask g 對象確保請求期間單例

##### `render_template(template_name, **context)`
渲染模板並自動注入比賽標題等全局變量

---

### 🛠️ utils.py - 工具函數

提供系統所需的各種工具函數和數據結構。

#### 核心函數

##### `get_hostm_ip()`
獲取主機IP地址
- **用途**：用於生成QR碼和網路存取
- **返回**：`str` - 主機IP地址
- **實現**：通過連接外部DNS獲取本機IP

##### `get_match_uuid(participant1, participant2)`
生成比賽唯一識別碼
- **參數**：
  - `participant1`: 參賽者1名稱
  - `participant2`: 參賽者2名稱
- **返回**：`str` - UUID格式的比賽ID
- **特點**：
  - 使用時間戳確保唯一性
  - 使用UUID5算法生成穩定ID
  - 基於命名空間 `NAMESPACE_MATCH`

##### `compile_player_data(players, matches, games)`
編譯選手比賽數據
- **參數**：
  - `players`: 選手列表
  - `matches`: 比賽記錄  
  - `games`: 局數記錄
- **返回**：`PlayerData` - 編譯後的選手數據
- **功能**：
  - 計算每位選手的勝負統計
  - 建立選手ID映射
  - 統計總勝場、勝局、勝分等數據

#### 數據結構

##### `PlayerData` (dataclass)
選手比賽數據的結構化存儲
```python
@dataclass
class PlayerData:
    nickname_id: dict[str, int]           # 暱稱到ID的映射
    match_res: dict[str, list]            # 比賽結果詳情
    match_list: list[list[str]]           # 每位選手的比賽清單
    tw_match: npt.NDArray[np.int8]        # 總勝場數
    tw_game: npt.NDArray[np.int8]         # 總勝局數  
    tl_game: npt.NDArray[np.int8]         # 總負局數
    tw_point: npt.NDArray[np.int8]        # 總勝分數
    tl_point: npt.NDArray[np.int8]        # 總負分數
```

**字段說明**：
- `match_res` 格式：`{match_id: [p1_win_game, p2_win_game, p1_point, p2_point, p1_nickname, p2_nickname]}`
- 所有數組使用 NumPy int8 類型節省記憶體
- `match_list[i]` 包含第i位選手參與的所有比賽ID

---

### 💾 db.py - 數據庫管理類

基於文件的簡單數據庫系統，支援事務和多程序安全。

#### DB 類核心方法

##### `__init__()`
初始化數據庫
- **功能**：
  - 創建數據存儲目錄 `data/`
  - 初始化多程序鎖
  - 定義支援的數據桶（buckets）
  - 根據比賽格式動態添加相應桶

**支援的數據桶**：
- `players`: 選手資訊
- `matches`: 比賽記錄
- `games`: 局數記錄  
- `game_in_progress`: 進行中的比賽
- `schedules`: 賽程安排
- `ranking`: 排名結果
- `groups`: 分組資訊（分組賽模式）
- `kntree`: 淘汰賽對戰樹（淘汰賽模式）

##### `save(bucket, data)`
保存數據到指定桶
- **參數**：
  - `bucket`: 數據桶名稱
  - `data`: 要保存的數據（dict格式）
- **特點**：
  - 追加模式寫入，保留歷史記錄
  - 自動加鎖確保線程安全
  - JSON格式存儲

##### `load(bucket, load_last=False)`
從指定桶載入數據
- **參數**：
  - `bucket`: 數據桶名稱
  - `load_last`: 是否只載入最新一筆記錄
- **返回**：`list[dict[str, Any]]` - 數據列表
- **行為**：
  - `load_last=True`: 返回最新一筆記錄，桶為空時返回 `[{}]`
  - `load_last=False`: 返回所有歷史記錄，桶為空時返回 `[]`

##### `transact(buckets, func, load_last_list=None)`
執行原子性事務操作
- **參數**：
  - `buckets`: 涉及的數據桶列表
  - `func`: 事務函數，簽名為 `(*datas) -> dict[str, dict[str, Any]]`
  - `load_last_list`: 每個桶是否只載入最新記錄的布林列表
- **返回**：
  - 成功：`None`
  - 失敗：錯誤訊息字符串
- **事務特性**：
  - 全加鎖確保原子性
  - 支援回滾（通過 `DeclineTransaction` 異常）
  - 批次更新多個桶

**事務函數範例**：
```python
def transaction_func(*datas):
    # datas[0] 是第一個桶的數據
    # datas[1] 是第二個桶的數據
    
    # 執行業務邏輯
    # 如果需要取消本次交易，拋出 DeclineTransaction(返回值)
    # 返回值會經由 db.transact() 函數返回
    
    return {
        'bucket1': new_data1,
        'bucket2': new_data2
    }
```

##### `is_empty(bucket)`
檢查數據桶是否為空
- **參數**：`bucket` - 數據桶名稱
- **返回**：`bool` - 桶是否為空
- **用途**：判斷比賽狀態、初始化檢查

##### `clear(bucket)`
清空指定數據桶
- **參數**：`bucket` - 數據桶名稱
- **功能**：刪除對應的數據文件
- **注意**：不可恢復操作

#### 多程序安全注意事項

⚠️ **重要**：本系統使用 `multiprocessing.Lock()` 確保多程序安全，在使用時需注意：

1. **鎖的作用範圍**：
   - 所有後綴不包含 `unchecked` 的函數都會自動加鎖
   - 鎖覆蓋整個操作期間，確保數據一致性

2. **避免死鎖**：
   - 不要在事務函數內部調用其他DB操作
   - 避免巢狀事務調用
   - 事務函數應盡量簡潔高效

3. **性能考量**：
   - 鎖會序列化所有DB操作
   - 適合中小型比賽，大規模使用需考慮性能優化
   - 建議事務函數避免耗時操作

5. **數據一致性**：
   - 事務內的所有變更要麼全部成功，要麼全部失敗
   - 使用 `DeclineTransaction` 實現回滾
   - 系統會自動處理並發訪問衝突

---

## 🔧 配置說明

### tbt_config.py
系統配置文件，包含以下重要參數：

```python
COMPETITION_TITLE = "你的比賽名稱"

GAMES_PER_MATH = 3

WINNING_SCORE = 11

# "group" or "knockout"
COMPETITION_FORMAT = "knockout"

# 只需在循環賽模式設定
GROUP_COUNT = 2

# 只需在淘汰賽模式設定
# "random" or "ordered"
KNOCKOUT_SEEDING = "random" 

# 如果為 None 預設為 8080
SERVER_PORT = None
```

## 🧪 測試

- 使用 `pytest` 進行單元測試 
- 目前只覆蓋 `core.py`

## 📱 用戶介面

系統提供美觀的響應式用戶介面：

- **選手註冊**：簡潔的註冊表單，即時驗證
- **比賽創建**：智能選手選擇，防止重複比賽
- **計分板**：專業桌球計分介面，支援換場和發球規則
- **排名展示**：動態排名榜，金銀銅獎牌效果
- **結果頁面**：美觀的結果展示，慶祝動畫

## 📄 授權

本專案為開源專案，歡迎貢獻和改進！

---

*Generated by TBT-SYS Documentation Generator*

*Modified by revival0728*
