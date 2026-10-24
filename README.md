# ✈️ 機票清艙與 Bug 價雷達 LINE 官方帳號 (Flight Clearance & Bug Fare Radar Bot)

> **致敬豬隊友 Scott / 布萊 N 機票達人 / Skyscanner LINE 推播，並整合「一鍵從機票生成旅遊行程」無縫閉環的次世代機票情報雷達！**

---

## 🌟 核心亮點與三大情報引擎

### 1. 🔥 Bug 價與破盤促銷雷達 (`app/radar_engine.py`)
- **豬隊友 Scott / 布萊 N 達人短評風格**：即時攔截傳統航空外站漏油稅 Bug 價（如國泰東京含稅 NT$6,850、長榮直飛巴黎含稅 NT$14,900）與廉航破盤閃促。
- **🌡️ 真假特價溫度計**：每張機票自動對比歷史均價，計算「省下金額」、「折數」與視覺化熱度進度條，並標註評級：
  - `🔥🔥🔥 史詩級 Bug 價`（低於歷史均價 48%，閉眼直接刷卡）
  - `⚡ 破盤神價`（年度前 5% 低價）
  - `🟢 值得入手好價`
  - `🟡 一般促銷 (建議觀望)`

### 2. ⚡ 旅行社清艙計畫票 / 晚鳥神秘票 (`app/radar_engine.py`)
- 專攻未來 **14 天內出發**、各大旅行社（雄獅、可樂、五福、易遊網）包機切位或退團釋出的「清艙計畫機票」。
- 全面包含 **20kg~23kg 免費托運行李**，並即時標示「剩餘最後 X 席」與出發倒數天數。

### 3. 🔍 Skyscanner 風格跨航司航線比價與「廉航含行李真實總價」試算 (`app/radar_engine.py`)
- 支援在 LINE 直接輸入目的地（如 `東京`、`大阪`、`沖繩`、`首爾`、`曼谷`、`歐洲` 或 `比價 東京`）。
- **防範廉航隱藏費用陷阱**：自動將廉價航空（虎航、樂桃、酷航、泰越捷等）加購來回 20kg 托運行李與選位餐點後的「真實總成本」與傳統航空（國泰、長榮、星宇、華航）同台PK，當廉航加完行李反而比傳統航空貴時，自動標示 `⚠️ 廉航加行李反貴陷阱`！

### 4. ✨ 獨家閉環：一鍵從機票生成完整旅遊行程 (`app/itinerary_bridge.py`)
- 每張機票登機證 Flex Message 卡片下方除了「🚀 前往搶票」與「🔔 訂閱此航線降價通知」外，皆配置一顆專屬 Postback 按鈕：
  - **「✨ 用此航班時間排行程」** (`action=plan_trip&deal_id=...`)
- 點擊後自動依據該機票的 **「目的地機場、旅遊天數、去程抵達時間（紅眼/早班機/午班機/晚班機）、回程起飛時間」**，透過 Google Gemini API（並內建完整高品質本地航班時段行程生成 Fallback，無 API Key 也能完美運行）生成：
  1. **第一天落地與最後一天返程的黃金時段調度攻略**
  2. **機場出關進市區最快交通方式（如 Skyliner / HARUKA / AREX / 單軌電車）与推薦住宿圈**
  3. **完美貼合去回程航班起降時間的每日早/午/晚不走回頭路行程表**

### 5. 🔔 個人化航線與價格門檻訂閱雷達 (`app/subscription_service.py` + `static/liff_radar.html`)
- **LINE 對話快捷指令**：
  - `訂閱 東京 6000` / `訂閱 沖繩 4000`
  - `訂閱 Bug價` / `訂閱 清艙`
  - `我的訂閱`
  - `取消訂閱 東京`
- **LIFF 視覺化控台 (`/liff`)**：支援一鍵勾選多條航線、自訂價格天花板、開啟全網 Bug 價警報與艙等偏好。
- **排程推播端點 (`POST /api/cron/push-radar`)**：供 GitHub Actions / Cron-job 定時觸發推播。

---

## 📂 專案目錄結構

```text
flight-bug-radar-bot/
├── app/
│   ├── __init__.py
│   ├── config.py                 # 環境變數與路徑配置
│   ├── radar_engine.py           # 三大機票情報引擎 (Bug價/清艙票/含行李真實總價試算)
│   ├── itinerary_bridge.py       # ✨ 一鍵從機票航班時間生成每日行程閉環引擎
│   ├── subscription_service.py   # 個人化航線目標價與 Bug 價訂閱服務
│   ├── flex_templates.py         # 登機證風格 Flex Message Carousel 與行程卡片模板
│   ├── bot_handler.py            # LINE Webhook 文字指令與 Postback 路由器
│   └── main.py                   # FastAPI 應用程式與 API 端點
├── api/
│   └── index.py                  # Vercel Serverless 入口
├── static/
│   └── liff_radar.html           # 個人化降價雷達 LIFF 設定網頁
├── setup_rich_menu.py            # 6 宮格高質感圖文選單自動繪製與部署腳本
├── test_radar_bot.py             # 完整單元與整合測試套件
├── main.py                       # 本地端快速啟動入口
├── requirements.txt
├── Dockerfile
├── render.yaml
├── vercel.json
└── .env.example
```

---

## 🚀 快速啟動與測試

```bash
# 1. 執行單元與整合測試
python -m unittest discover -s . -p "test_radar_bot.py" -v

# 2. 啟動 FastAPI 伺服器
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
