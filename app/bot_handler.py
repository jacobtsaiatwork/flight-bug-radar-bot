"""
LINE Webhook 事件與對話路由器 (Bot Handler)
整合：
- 文字指令路由 (Bug 價雷達、清艙晚鳥票、Skyscanner 航線含行李真實總價試算、飛哪裡最便宜、訂閱管理、直接從機票排行程)
- Postback 事件路由：
  1. `action=plan_trip&deal_id=...` -> 一鍵從該張機票的起降時間與天數生成完整每日行程卡片
  2. `action=subscribe_route&dest=...&max_price=...` -> 一鍵訂閱該航線降價通知
"""

import urllib.parse
from typing import Dict, Any, Optional, List
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, PostbackEvent

from app.config import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, IS_MOCK_MODE
from app.radar_engine import radar_engine
from app.itinerary_bridge import itinerary_bridge
from app.subscription_service import subscription_service
from app.flex_templates import (
    create_deals_carousel_flex,
    create_route_comparison_flex,
    create_flight_itinerary_flex,
    create_subscription_status_flex,
)

handler = WebhookHandler(LINE_CHANNEL_SECRET or "mock_secret_for_local_dev")


def get_messaging_api() -> Optional[MessagingApi]:
    if IS_MOCK_MODE or not LINE_CHANNEL_ACCESS_TOKEN:
        return None
    config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
    client = ApiClient(config)
    return MessagingApi(client)


def build_default_quick_reply() -> QuickReply:
    options = [
        ("🔥 今日 Bug 價雷達", "Bug價雷達"),
        ("⚡ 14天內清艙票", "清艙晚鳥票"),
        ("🔍 東京含行李真比價", "比價 東京"),
        ("🔍 大阪含行李真比價", "比價 大阪"),
        ("🌍 飛哪裡最便宜", "飛哪裡最便宜"),
        ("🔔 我的降價訂閱", "我的訂閱"),
    ]
    return QuickReply(
        items=[
            QuickReplyItem(action=MessageAction(label=label, text=text))
            for label, text in options
        ]
    )


def handle_user_text_logic(user_id: str, text: str) -> Dict[str, Any]:
    """
    核心文字訊息處理邏輯 (同時供 LINE Webhook 與 `/api/simulate-chat`、單元測試呼叫)
    回傳結構: {"type": "flex" | "text", "alt_text": str, "flex": dict, "text": str}
    """
    msg = text.strip()
    low = msg.lower()

    # 1. 優先檢查是否為訂閱/退訂指令 (例如：「訂閱 東京 6000」、「取消訂閱 東京」)
    sub_cmd_res = subscription_service.parse_and_execute_command(user_id, msg)
    if sub_cmd_res:
        sub_flex = create_subscription_status_flex(sub_cmd_res["subscription"])
        return {
            "type": "flex",
            "alt_text": sub_cmd_res["message"],
            "text": sub_cmd_res["message"],
            "flex": sub_flex,
            "subscription_result": sub_cmd_res,
        }

    # 2. 查看「我的訂閱」/「訂閱設定」
    if msg in ["我的訂閱", "訂閱", "訂閱設定", "降價通知", "推播設定"]:
        sub = subscription_service.get_subscription(user_id)
        return {
            "type": "flex",
            "alt_text": "🔔 我的航線降價與 Bug 價訂閱雷達",
            "text": "🔔 這是您目前的航線目標價與 Bug 價推播設定：",
            "flex": create_subscription_status_flex(sub),
        }

    # 3. ⚡ 旅行社清艙計畫票 / 晚鳥神秘票
    if any(k in low for k in ["清艙", "晚鳥", "計畫票", "神秘票", "最後機位", "clearance"]):
        dest_code = radar_engine.resolve_dest_code(msg)
        deals = radar_engine.get_clearance_deals(dest_filter=dest_code)
        if not deals:
            deals = radar_engine.get_clearance_deals()
        return {
            "type": "flex",
            "alt_text": "⚡ 旅行社 14 天內清艙計畫票與晚鳥神秘票",
            "text": "⚡ 為您掃描全台各大旅行社（雄獅/可樂/五福/易遊網）未來 14 天內出發的【清艙計畫票】，全部已含 20~23kg 托運行李！點擊下方『✨ 用此航班時間排行程』可一鍵生成行程：",
            "flex": create_deals_carousel_flex(deals),
            "deals": deals,
        }

    # 4. 🌍 飛哪裡最便宜 (全網低價排行)
    if any(k in low for k in ["飛哪裡最便宜", "哪裡最便宜", "最便宜", "everywhere", "低價排行"]):
        ranked = radar_engine.get_everywhere_cheapest_ranking()
        return {
            "type": "flex",
            "alt_text": "🌍 飛哪裡最便宜：全航線破盤底價排行榜",
            "text": "🌍 為您依含稅總價由低到高排出【飛哪裡最便宜】全航線排行榜！看到心動價格可直接點『✨ 用此航班時間排行程』：",
            "flex": create_deals_carousel_flex(ranked),
            "deals": ranked,
        }

    # 5. ✨ 直接以文字要求用某張機票或目的地排行程
    if "排行程" in msg or "生成行程" in msg:
        dest_code = radar_engine.resolve_dest_code(msg) or "NRT"
        deals = radar_engine.get_bug_and_promo_deals(dest_filter=dest_code) + radar_engine.get_clearance_deals(dest_filter=dest_code)
        target_deal_id = deals[0]["deal_id"] if deals else "BUG-CX-NRT-01"
        itin = itinerary_bridge.generate_itinerary_from_deal(target_deal_id)
        return {
            "type": "flex",
            "alt_text": f"✨ 【{itin['city']} {itin['days_count']}天】貼合航班時間專屬行程",
            "text": itin["ai_summary"],
            "flex": create_flight_itinerary_flex(itin),
            "itinerary": itin,
        }

    # 6. 🔍 Skyscanner 風格跨航司比價與廉航含行李真實總價試算 (當輸入包含「比價」、「試算」或直接輸入目的地如「東京」、「大阪」、「沖繩」、「首爾」、「曼谷」、「歐洲」)
    dest_code = radar_engine.resolve_dest_code(msg)
    if dest_code or any(k in low for k in ["比價", "真實總價", "廉航", "行李試算", "skyscanner"]):
        comp = radar_engine.compare_route_true_cost(msg, include_baggage=True)
        return {
            "type": "flex",
            "alt_text": f"🔍 台北飛【{comp['city']}】跨航司含 20kg 托運行李真實總價比價",
            "text": comp["trap_warning"],
            "flex": create_route_comparison_flex(comp),
            "comparison": comp,
        }

    # 7. 預設 / 🔥 Bug 價與破盤促銷雷達
    deals = radar_engine.get_bug_and_promo_deals()
    return {
        "type": "flex",
        "alt_text": "🔥 今日全網機票 Bug 價與破盤促銷雷達",
        "text": "🔥 【機票清艙與 Bug 價雷達】為您攔截今日最新傳統航空 Bug 價與破盤閃促！每張機票皆附『真假特價溫度計』，並支援一鍵點擊『✨ 用此航班時間排行程』：",
        "flex": create_deals_carousel_flex(deals),
        "deals": deals,
    }


def handle_postback_logic(user_id: str, postback_data: str) -> Dict[str, Any]:
    """
    處理 LINE Postback 事件資料：
    - `action=plan_trip&deal_id=BUG-CX-NRT-01` -> 觸發 `itinerary_bridge` 生成貼合該航班時間的完整旅遊行程 Flex 卡片
    - `action=subscribe_route&dest=NRT&max_price=6850` -> 觸發 `subscription_service` 訂閱該航線降價通知
    """
    params = dict(urllib.parse.parse_qsl(postback_data))
    action = params.get("action", "")

    if action == "plan_trip":
        deal_id = params.get("deal_id", "BUG-CX-NRT-01")
        itin = itinerary_bridge.generate_itinerary_from_deal(deal_id)
        flex_card = create_flight_itinerary_flex(itin)
        return {
            "type": "flex",
            "action": "plan_trip",
            "deal_id": deal_id,
            "alt_text": f"✨ 已根據【{itin['airline']} {itin['city']}】航班時間生成 {itin['days_count']} 天專屬行程！",
            "text": itin["ai_summary"],
            "flex": flex_card,
            "itinerary": itin,
        }

    if action == "subscribe_route":
        dest = params.get("dest", "NRT")
        max_price_str = params.get("max_price", "7000")
        try:
            max_price = int(max_price_str)
        except ValueError:
            max_price = 7000
        res = subscription_service.subscribe_route(user_id, dest, max_price)
        return {
            "type": "flex",
            "action": "subscribe_route",
            "alt_text": res["message"],
            "text": res["message"],
            "flex": create_subscription_status_flex(res["subscription"]),
            "subscription_result": res,
        }

    # 預設回傳 Bug 價雷達
    deals = radar_engine.get_bug_and_promo_deals()
    return {
        "type": "flex",
        "action": "default",
        "alt_text": "🔥 最新機票 Bug 價雷達",
        "text": "🔥 最新機票 Bug 價雷達：",
        "flex": create_deals_carousel_flex(deals),
    }


@handler.add(MessageEvent, message=TextMessageContent)
def on_text_message(event: MessageEvent):
    user_id = getattr(event.source, "user_id", "line_user_default")
    res = handle_user_text_logic(user_id, event.message.text)
    api = get_messaging_api()
    if not api:
        return

    qr = build_default_quick_reply()
    messages = []
    if res.get("text"):
        messages.append(TextMessage(text=res["text"]))
    if res.get("flex"):
        messages.append(
            FlexMessage(
                alt_text=res.get("alt_text", "✈️ 機票清艙與 Bug 價雷達"),
                contents=FlexContainer.from_dict(res["flex"]),
                quick_reply=qr,
            )
        )
    elif messages:
        messages[-1].quick_reply = qr

    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=messages[:5]))


@handler.add(PostbackEvent)
def on_postback_event(event: PostbackEvent):
    user_id = getattr(event.source, "user_id", "line_user_default")
    data = event.postback.data or ""
    res = handle_postback_logic(user_id, data)
    api = get_messaging_api()
    if not api:
        return

    qr = build_default_quick_reply()
    messages = []
    if res.get("text"):
        messages.append(TextMessage(text=res["text"]))
    if res.get("flex"):
        messages.append(
            FlexMessage(
                alt_text=res.get("alt_text", "✨ 航班專屬行程與雷達通知"),
                contents=FlexContainer.from_dict(res["flex"]),
                quick_reply=qr,
            )
        )
    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=messages[:5]))
