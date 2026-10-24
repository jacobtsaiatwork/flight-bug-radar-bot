"""
FastAPI 主應用程式 (Flight Clearance & Bug Fare Radar Bot)
提供：
- `POST /callback` : LINE Messaging API Webhook 端點
- `GET /liff` : 個人化航線與價格門檻訂閱雷達 LIFF 頁面
- `GET /api/radar/bug-fares` : 取得 Bug 價與破盤促銷情報
- `GET /api/radar/clearance` : 取得旅行社 14 天內清艙計畫票 / 晚鳥神秘票
- `GET /api/radar/compare` : Skyscanner 風格跨航司比價與廉航含行李真實總價試算
- `POST /api/itinerary/from-deal` : ✨ 一鍵從機票生成完整旅遊行程閉環 API
- `GET /api/subscriptions/{user_id}` & `POST /api/subscriptions` : 訂閱管理 API
- `POST /api/cron/push-radar` : 排程自動化推播最新 Bug 價與清艙票端點
- `POST /api/simulate-chat` & `POST /api/simulate-postback` : 本地端與自動化測試專用模擬器
"""

from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import PushMessageRequest, FlexMessage, FlexContainer

from app.config import (
    STATIC_DIR,
    IS_MOCK_MODE,
    CRON_SECRET,
    PORT,
)
from app.radar_engine import radar_engine
from app.itinerary_bridge import itinerary_bridge
from app.subscription_service import subscription_service
from app.bot_handler import (
    handler,
    get_messaging_api,
    handle_user_text_logic,
    handle_postback_logic,
)
from app.flex_templates import create_deals_carousel_flex

app = FastAPI(
    title="✈️ 機票清艙與 Bug 價雷達 LINE Bot API",
    description="致敬豬隊友 Scott / 布萊 N 機票達人 / Skyscanner 推播，並整合一鍵從機票生成旅遊行程閉環",
    version="1.0.0",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SubscriptionPayload(BaseModel):
    user_id: str = "guest_radar_user"
    routes: Dict[str, int] = {"NRT": 7500, "KIX": 8500}
    bug_fare_alert: bool = True
    clearance_alert: bool = True
    cabin_pref: str = "economy"
    include_baggage_only: bool = True


class SimulateChatPayload(BaseModel):
    user_id: str = "test_user_001"
    message: str


class SimulatePostbackPayload(BaseModel):
    user_id: str = "test_user_001"
    data: str


class PlanFromDealPayload(BaseModel):
    deal_id: str = "BUG-CX-NRT-01"


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>✈️ 機票清艙與 Bug 價雷達 LINE Bot</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-white min-h-screen flex items-center justify-center p-4">
      <div class="max-w-lg w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl">
        <div class="text-5xl mb-3">✈️🔥</div>
        <h1 class="text-2xl font-black mb-2">機票清艙與 Bug 價雷達 LINE Bot</h1>
        <p class="text-xs text-slate-400 mb-6">豬隊友 Scott / 布萊 N 達人風格 × Skyscanner 含行李真實總價試算 × 一鍵從機票排行程閉環</p>
        <div class="space-y-3">
          <a href="/liff" class="block w-full py-3 bg-rose-600 hover:bg-rose-500 rounded-xl font-bold text-sm">🎛️ 開啟 LIFF 降價訂閱雷達面板</a>
          <a href="/docs" class="block w-full py-3 bg-slate-800 hover:bg-slate-700 rounded-xl font-semibold text-sm text-slate-200">📖 查看 OpenAPI / Swagger 互動文件</a>
        </div>
      </div>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "flight-bug-radar-bot",
        "mock_mode": IS_MOCK_MODE,
        "bug_deals_count": len(radar_engine.get_bug_and_promo_deals()),
        "clearance_deals_count": len(radar_engine.get_clearance_deals()),
    }


@app.get("/liff")
async def serve_liff_radar():
    liff_file = STATIC_DIR / "liff_radar.html"
    if liff_file.exists():
        return FileResponse(str(liff_file))
    raise HTTPException(status_code=404, detail="LIFF page not found")


@app.get("/api/radar/bug-fares")
async def api_get_bug_fares(dest: Optional[str] = None, max_price: Optional[int] = None):
    deals = radar_engine.get_bug_and_promo_deals(dest_filter=dest, max_price=max_price)
    return {"count": len(deals), "deals": deals}


@app.get("/api/radar/clearance")
async def api_get_clearance_deals(dest: Optional[str] = None, max_days: int = 14):
    deals = radar_engine.get_clearance_deals(dest_filter=dest, max_days_until_dep=max_days)
    return {"count": len(deals), "deals": deals}


@app.get("/api/radar/compare")
async def api_compare_route(dest: str = "東京", include_baggage: bool = True):
    comp = radar_engine.compare_route_true_cost(dest, include_baggage=include_baggage)
    return comp


@app.post("/api/itinerary/from-deal")
async def api_generate_itinerary_from_deal(payload: PlanFromDealPayload):
    itin = itinerary_bridge.generate_itinerary_from_deal(payload.deal_id)
    return itin


@app.get("/api/subscriptions/{user_id}")
async def api_get_subscription(user_id: str):
    return subscription_service.get_subscription(user_id)


@app.post("/api/subscriptions")
async def api_update_subscription(payload: SubscriptionPayload):
    sub = subscription_service.update_from_liff(
        user_id=payload.user_id,
        routes=payload.routes,
        bug_fare_alert=payload.bug_fare_alert,
        clearance_alert=payload.clearance_alert,
        cabin_pref=payload.cabin_pref,
        include_baggage_only=payload.include_baggage_only,
    )
    matched = subscription_service.match_deals_for_user(payload.user_id)
    return {
        "status": "success",
        "subscription": sub,
        "matched_deals_count": len(matched),
        "matched_deals": matched,
    }


@app.post("/api/cron/push-radar")
async def api_cron_push_radar(
    cron_key: Optional[str] = Query(None),
    x_cron_key: Optional[str] = Header(None),
):
    """排程推播端點：自動比對所有訂閱者的價格門檻與 Bug 價設定並發送推播"""
    if CRON_SECRET:
        token = cron_key or x_cron_key
        if token != CRON_SECRET:
            raise HTTPException(status_code=403, detail="Invalid CRON_SECRET")

    subscribers = subscription_service.get_all_subscribers()
    if not subscribers:
        # 確保至少有一筆預設訂閱者可供展示
        subscription_service.get_subscription("demo_subscriber_01")
        subscribers = subscription_service.get_all_subscribers()

    api = get_messaging_api()
    pushed_records = []

    for sub in subscribers:
        uid = sub["user_id"]
        matched_deals = subscription_service.match_deals_for_user(uid)
        if not matched_deals:
            continue

        flex_dict = create_deals_carousel_flex(matched_deals[:5])
        if api and uid.startswith("U"):
            try:
                api.push_message(
                    PushMessageRequest(
                        to=uid,
                        messages=[
                            FlexMessage(
                                alt_text="🔥 機票雷達警報：發現符合您目標預算的 Bug 價與清艙神價！",
                                contents=FlexContainer.from_dict(flex_dict),
                            )
                        ],
                    )
                )
                pushed_records.append({"user_id": uid, "status": "pushed", "deals_count": len(matched_deals)})
            except Exception as e:
                pushed_records.append({"user_id": uid, "status": "error", "error": str(e)})
        else:
            pushed_records.append(
                {
                    "user_id": uid,
                    "status": "mock_pushed",
                    "deals_count": len(matched_deals),
                    "top_deal": matched_deals[0]["deal_id"],
                }
            )

    return {
        "status": "completed",
        "total_subscribers_checked": len(subscribers),
        "pushed_count": len(pushed_records),
        "records": pushed_records,
    }


@app.post("/api/simulate-chat")
async def api_simulate_chat(payload: SimulateChatPayload):
    return handle_user_text_logic(payload.user_id, payload.message)


@app.post("/api/simulate-postback")
async def api_simulate_postback(payload: SimulatePostbackPayload):
    return handle_postback_logic(payload.user_id, payload.data)


@app.post("/callback")
async def line_webhook_callback(
    request: Request,
    x_line_signature: Optional[str] = Header(None),
):
    body = (await request.body()).decode("utf-8")
    if IS_MOCK_MODE:
        return JSONResponse(content={"status": "mock_ok"})

    if not x_line_signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature")

    try:
        handler.handle(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return JSONResponse(content={"status": "ok"})
