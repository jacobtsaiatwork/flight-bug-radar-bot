"""
🎨 高質感 LINE Flex Message 模板生成器 (Flex Templates)
包含：
1. 機票登機證 (Boarding Pass) 視覺風格的 Flex Message Carousel (含真假特價溫度計進度條、Postback「✨ 用此航班時間排行程」、Postback「🔔 訂閱此航線降價通知」、URI「🚀 前往搶票」)
2. Skyscanner 風格跨航司比價與廉航含行李真實總價試算卡片 (防坑警示 + 一鍵排行程)
3. ✨ 獨家閉環：貼合航班起降時間的完整多日旅遊行程、機場交通與住宿建議 Flex Message
4. 🔔 個人化航線與價格門檻訂閱管理卡片 (含 LIFF 視覺化設定按鈕)
"""

import urllib.parse
from typing import List, Dict, Any, Optional


def clean_uri(url: str) -> str:
    if not url:
        return "https://www.skyscanner.com.tw"
    parts = urllib.parse.urlsplit(url)
    encoded_path = urllib.parse.quote(parts.path, safe="/")
    encoded_query = urllib.parse.quote(parts.query, safe="=&+?:/%")
    return urllib.parse.urlunsplit((parts.scheme or "https", parts.netloc, encoded_path, encoded_query, parts.fragment))


def build_boarding_pass_bubble(deal: Dict[str, Any]) -> Dict[str, Any]:
    """建立單張機票登機證 (Boarding Pass) 風格 Flex Bubble"""
    is_clearance = deal.get("category") == "clearance"
    is_bug = deal.get("category") == "bug_fare"

    header_bg = "#B71C1C" if is_bug else ("#E65100" if is_clearance else "#0D47A1")
    top_tag = (
        f"🚨 旅行社晚鳥清艙・剩最後 {deal.get('seats_left', 3)} 席"
        if is_clearance
        else deal.get("thermometer_grade", "🔥 破盤神價")
    )

    price = deal.get("total_price_tax_included", 0)
    hist_price = deal.get("historical_avg_price", 12000)
    saved = deal.get("saved_amount", max(0, hist_price - price))
    fold = deal.get("discount_fold", 5.0)
    bar_pct = deal.get("bar_percent", 85)
    badge_color = deal.get("badge_color", "#D32F2F")

    sub_header_text = (
        f"{deal.get('agency', '')} × {deal.get('airline', '')}"
        if is_clearance
        else f"{deal.get('airline', '')} · {deal.get('cabin', '經濟艙')}"
    )

    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": header_bg,
            "paddingAll": "14px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "text",
                            "text": top_tag,
                            "color": "#FFD54F",
                            "size": "xs",
                            "weight": "bold",
                            "flex": 7,
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": f"省 ${saved:,} ({fold}折)",
                            "color": "#FFFFFF",
                            "size": "xxs",
                            "weight": "bold",
                            "align": "end",
                            "flex": 4,
                        },
                    ],
                },
                {
                    "type": "text",
                    "text": sub_header_text,
                    "color": "#FFFFFF",
                    "size": "xs",
                    "margin": "xs",
                    "wrap": True,
                },
                # 登機證航線大字展示 (TPE ✈️ NRT)
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 3,
                            "contents": [
                                {"type": "text", "text": deal.get("origin", "TPE"), "color": "#FFFFFF", "size": "xl", "weight": "bold"},
                                {"type": "text", "text": deal.get("origin_name", "台北桃園"), "color": "#FFCDD2", "size": "xxs"},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 4,
                            "alignItems": "center",
                            "contents": [
                                {"type": "text", "text": f"✈️ {deal.get('days', 5)}天來回", "color": "#FFE082", "size": "xxs", "weight": "bold"},
                                {"type": "text", "text": "──────", "color": "#FFFFFF", "size": "xs"},
                                {"type": "text", "text": deal.get("flight_slot_type", "直飛航班"), "color": "#FFFFFF", "size": "xxs"},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "flex": 3,
                            "alignItems": "end",
                            "contents": [
                                {"type": "text", "text": deal.get("dest", "NRT"), "color": "#FFFFFF", "size": "xl", "weight": "bold"},
                                {"type": "text", "text": deal.get("dest_name", "東京成田"), "color": "#FFCDD2", "size": "xxs"},
                            ],
                        },
                    ],
                },
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "14px",
            "contents": [
                # 價格與歷史均價對比
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "baseline",
                    "contents": [
                        {"type": "text", "text": "來回含稅", "size": "xs", "color": "#616161", "flex": 2},
                        {"type": "text", "text": f"NT$ {price:,}", "size": "xl", "weight": "bold", "color": "#D32F2F", "flex": 5},
                        {"type": "text", "text": f"均價 ${hist_price:,}", "size": "xxs", "color": "#9E9E9E", "decoration": "line-through", "align": "end", "flex": 3},
                    ],
                },
                # 真假特價溫度計進度條
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "margin": "xs",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "🌡️ 真假特價溫度計", "size": "xxs", "color": "#424242", "weight": "bold", "flex": 5},
                                {"type": "text", "text": f"激省熱度 {bar_pct}%", "size": "xxs", "color": badge_color, "weight": "bold", "align": "end", "flex": 4},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#EEEEEE",
                            "height": "6px",
                            "cornerRadius": "3px",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": badge_color,
                                    "width": f"{bar_pct}%",
                                    "height": "6px",
                                    "cornerRadius": "3px",
                                    "contents": [],
                                }
                            ],
                        },
                    ],
                },
                {"type": "separator", "margin": "sm"},
                # 航班時間與行李資訊
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "xs",
                    "margin": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"🛫 去程：{deal.get('flight_no_out', '')} ({deal.get('dep_time_out', '')} → {deal.get('arr_time_out', '')})",
                            "size": "xs",
                            "color": "#212121",
                            "weight": "bold",
                        },
                        {
                            "type": "text",
                            "text": f"🛬 回程：{deal.get('flight_no_in', '')} ({deal.get('dep_time_in', '')} → {deal.get('arr_time_in', '')})",
                            "size": "xs",
                            "color": "#212121",
                            "weight": "bold",
                        },
                        {
                            "type": "text",
                            "text": f"🧳 行李：{deal.get('baggage_detail', '含手提行李')}",
                            "size": "xxs",
                            "color": "#1B5E20" if deal.get("baggage_included") else "#E65100",
                            "weight": "bold",
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": f"📅 適用：{deal.get('travel_period', '近期出發')}",
                            "size": "xxs",
                            "color": "#555555",
                            "wrap": True,
                        },
                        {
                            "type": "text",
                            "text": deal.get("countdown_note", ""),
                            "size": "xxs",
                            "color": "#C62828",
                            "weight": "bold",
                            "wrap": True,
                        },
                    ],
                },
                # 達人短評
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#FFF8E1",
                    "cornerRadius": "6px",
                    "paddingAll": "8px",
                    "margin": "xs",
                    "contents": [
                        {
                            "type": "text",
                            "text": deal.get("expert_comment", ""),
                            "size": "xxs",
                            "color": "#4E342E",
                            "wrap": True,
                        }
                    ],
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "12px",
            "contents": [
                # 按鈕 1：前往搶票
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#D32F2F" if is_bug else "#1976D2",
                    "action": {
                        "type": "uri",
                        "label": "🚀 前往搶票 (Skyscanner/官網)",
                        "uri": clean_uri(deal.get("booking_url", "https://www.skyscanner.com.tw")),
                    },
                },
                # 按鈕 2 (核心閉環)：✨ 用此航班時間排行程 (Postback)
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#00897B",
                    "action": {
                        "type": "postback",
                        "label": "✨ 用此航班時間排行程",
                        "data": f"action=plan_trip&deal_id={deal.get('deal_id', 'BUG-CX-NRT-01')}",
                        "displayText": f"✨ 請幫我用【{deal.get('city', '東京')} {deal.get('airline', '')}】這張機票的航班時間排行程！",
                    },
                },
                # 按鈕 3：🔔 訂閱此航線降價通知 (Postback)
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": f"🔔 訂閱{deal.get('city', '此航線')}降價通知",
                        "data": f"action=subscribe_route&dest={deal.get('dest', 'NRT')}&max_price={price}",
                        "displayText": f"訂閱 {deal.get('city', '東京')} {price}",
                    },
                },
            ],
        },
    }


def create_deals_carousel_flex(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """產出機票登機證風格 Carousel Flex Message"""
    bubbles = [build_boarding_pass_bubble(d) for d in deals[:10]]
    return {
        "type": "carousel",
        "contents": bubbles,
    }


def create_route_comparison_flex(comparison_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    產出 🔍 Skyscanner 風格跨航司航線比價與廉航含行李真實總價試算 Flex Message
    """
    city = comparison_data.get("city", "東京")
    airport_name = comparison_data.get("airport_name", "國際機場")
    hist_avg = comparison_data.get("historical_avg_price", 14000)
    carriers = comparison_data.get("carriers", [])
    best = comparison_data.get("best_choice") or (carriers[0] if carriers else {})
    best_deal_id = best.get("deal_id", "BUG-CX-NRT-01")

    carrier_rows = []
    for idx, c in enumerate(carriers):
        is_top = idx == 0
        is_trap = c.get("is_lcc_trap", False)
        badge_text = "🏆 含行李最划算" if is_top else ("⚠️ 廉航加行李反貴陷阱" if is_trap else ("✈️ 傳統航空全包" if not c["is_lcc"] else "🎒 廉航加購試算"))
        badge_col = "#2E7D32" if is_top else ("#C62828" if is_trap else "#1565C0")

        carrier_rows.append(
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#F1F8E9" if is_top else ("#FFEBEE" if is_trap else "#F5F5F5"),
                "cornerRadius": "8px",
                "paddingAll": "10px",
                "margin": "sm",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "text", "text": badge_text, "size": "xxs", "weight": "bold", "color": badge_col, "flex": 5},
                            {"type": "text", "text": c.get("thermometer_grade", ""), "size": "xxs", "color": "#E65100", "align": "end", "flex": 5, "wrap": True},
                        ],
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "margin": "xs",
                        "alignItems": "baseline",
                        "contents": [
                            {"type": "text", "text": c.get("airline", ""), "size": "sm", "weight": "bold", "color": "#212121", "flex": 6, "wrap": True},
                            {"type": "text", "text": f"真實總價 ${c.get('true_total_with_baggage', 0):,}", "size": "sm", "weight": "bold", "color": "#D32F2F" if is_top else "#37474F", "align": "end", "flex": 4},
                        ],
                    },
                    {
                        "type": "text",
                        "text": f"票面含稅 ${c.get('base_fare_tax_included', 0):,} + 來回托運加購 ${c.get('baggage_fee_roundtrip', 0):,}",
                        "size": "xxs",
                        "color": "#616161",
                        "margin": "xs",
                    },
                    {
                        "type": "text",
                        "text": f"🧳 {c.get('baggage_allowance', '')} | 🕒 {c.get('flight_time', '')}",
                        "size": "xxs",
                        "color": "#455A64",
                        "wrap": True,
                    },
                ],
            }
        )

    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#0277BD",
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "🔍 Skyscanner 跨航司真實總價試算雷達", "color": "#B3E5FC", "size": "xs", "weight": "bold"},
                {"type": "text", "text": f"台北 ✈️ 【{city}】含 20kg 托運真實比價", "color": "#FFFFFF", "size": "lg", "weight": "bold", "margin": "xs", "wrap": True},
                {"type": "text", "text": f"{airport_name} | 歷史均價 NT${hist_avg:,}", "color": "#E1F5FE", "size": "xxs", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "contents": [
                *carrier_rows,
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#FFF3E0",
                    "cornerRadius": "6px",
                    "paddingAll": "10px",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": comparison_data.get("trap_warning", ""),
                            "size": "xxs",
                            "color": "#E65100",
                            "weight": "bold",
                            "wrap": True,
                        }
                    ],
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#0277BD",
                    "action": {
                        "type": "uri",
                        "label": f"🚀 前往搶購 {city} 冠軍底價機票",
                        "uri": clean_uri(best.get("booking_url", "https://www.skyscanner.com.tw")),
                    },
                },
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#00897B",
                    "action": {
                        "type": "postback",
                        "label": f"✨ 用【{city}】冠軍航班排行程",
                        "data": f"action=plan_trip&deal_id={best_deal_id}",
                        "displayText": f"✨ 請幫我用【{city}】最佳航班時間排行程！",
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": f"🔔 訂閱 {city} 降價通知",
                        "data": f"action=subscribe_route&dest={comparison_data.get('dest_code', 'NRT')}&max_price={best.get('true_total_with_baggage', 7000)}",
                        "displayText": f"訂閱 {city} {best.get('true_total_with_baggage', 7000)}",
                    },
                },
            ],
        },
    }


def create_flight_itinerary_flex(itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    產出 ✨ 一鍵從機票生成完整旅遊行程 Flex Message 卡片
    依據去程抵達時間與回程起飛時間，完整呈現每日早/午/晚動線、機場交通與住宿建議！
    """
    deal = itinerary_data.get("deal", {})
    city = itinerary_data.get("city", "東京")
    days_count = itinerary_data.get("days_count", 5)
    daily_plans = itinerary_data.get("daily_plans", [])

    day_boxes = []
    share_lines = [
        f"✈️ 【{city} {days_count}天航班專屬行程】",
        f"🎫 綁定航班：{itinerary_data.get('airline', '')} {itinerary_data.get('flight_summary', '')}",
        f"💰 機票含稅：NT${itinerary_data.get('total_price', 0):,}",
        "",
    ]

    for d in daily_plans:
        day_num = d.get("day", 1)
        theme = d.get("theme", "")
        day_boxes.append(
            {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#F8F9FA",
                "cornerRadius": "8px",
                "paddingAll": "10px",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": f"📅 Day {day_num}｜{theme}",
                        "size": "xs",
                        "weight": "bold",
                        "color": "#00695C",
                        "wrap": True,
                    },
                    {"type": "separator", "margin": "xs"},
                    {
                        "type": "text",
                        "text": f"🌅 上午：{d.get('morning', '')}",
                        "size": "xxs",
                        "color": "#37474F",
                        "margin": "xs",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": f"☀️ 下午：{d.get('afternoon', '')}",
                        "size": "xxs",
                        "color": "#37474F",
                        "margin": "xs",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": f"🌙 晚上：{d.get('evening', '')}",
                        "size": "xxs",
                        "color": "#37474F",
                        "margin": "xs",
                        "wrap": True,
                    },
                ],
            }
        )
        share_lines.append(f"Day {day_num}: {theme}")
        share_lines.append(f"  🌅 {d.get('morning', '')}")
        share_lines.append(f"  ☀️ {d.get('afternoon', '')}")
        share_lines.append(f"  🌙 {d.get('evening', '')}")

    share_lines.append("")
    share_lines.append(itinerary_data.get("airport_transit", ""))
    share_lines.append(itinerary_data.get("hotel_zone", ""))
    share_url = f"https://line.me/R/msg/text/?{urllib.parse.quote(chr(10).join(share_lines))}"
    map_search_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(city + ' 景點')}"

    return {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#00695C",
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "✨ 機票×行程無縫閉環｜AI 航班時段定制", "color": "#A7FFEB", "size": "xs", "weight": "bold"},
                {"type": "text", "text": f"✈️ 【{city} {days_count}天】貼合航班時間專屬行程", "color": "#FFFFFF", "size": "lg", "weight": "bold", "margin": "xs", "wrap": True},
                {"type": "text", "text": f"航班：{itinerary_data.get('airline', '')} {itinerary_data.get('flight_summary', '')}", "color": "#E0F2F1", "size": "xxs", "margin": "xs", "wrap": True},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "14px",
            "contents": [
                # 航班起降調度攻略盒
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#E0F2F1",
                    "cornerRadius": "8px",
                    "paddingAll": "10px",
                    "contents": [
                        {"type": "text", "text": itinerary_data.get("ai_summary", ""), "size": "xs", "weight": "bold", "color": "#004D40", "wrap": True},
                        {"type": "text", "text": itinerary_data.get("day1_strategy", ""), "size": "xxs", "color": "#00695C", "margin": "xs", "wrap": True},
                        {"type": "text", "text": itinerary_data.get("last_day_strategy", ""), "size": "xxs", "color": "#00695C", "margin": "xs", "wrap": True},
                    ],
                },
                # 機場交通與住宿建議
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#FFF8E1",
                    "cornerRadius": "8px",
                    "paddingAll": "10px",
                    "margin": "sm",
                    "contents": [
                        {"type": "text", "text": itinerary_data.get("airport_transit", ""), "size": "xxs", "color": "#E65100", "weight": "bold", "wrap": True},
                        {"type": "text", "text": itinerary_data.get("hotel_zone", ""), "size": "xxs", "color": "#4E342E", "margin": "xs", "wrap": True},
                    ],
                },
                # 每日行程清單
                *day_boxes,
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#D32F2F",
                    "action": {
                        "type": "uri",
                        "label": f"🚀 立即鎖定此張 NT${itinerary_data.get('total_price', 0):,} 機票",
                        "uri": clean_uri(deal.get("booking_url", "https://www.skyscanner.com.tw")),
                    },
                },
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#06C755",
                    "action": {
                        "type": "uri",
                        "label": "📲 一鍵轉發航班＋行程給旅伴討論",
                        "uri": clean_uri(share_url),
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": f"🗺️ 在 Google Maps 查看 {city} 景點地圖",
                        "uri": clean_uri(map_search_url),
                    },
                },
            ],
        },
    }


def create_subscription_status_flex(sub: Dict[str, Any], liff_url: str = "https://flight-bug-radar-bot.onrender.com/liff") -> Dict[str, Any]:
    """產出 🔔 個人化航線與價格門檻訂閱雷達設定卡片"""
    routes = sub.get("routes", {})
    route_items = []
    if routes:
        for code, info in routes.items():
            route_items.append(
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "xs",
                    "contents": [
                        {"type": "text", "text": f"✈️ {info.get('city', code)} ({code})", "size": "xs", "weight": "bold", "color": "#212121", "flex": 5},
                        {"type": "text", "text": f"低於 NT${info.get('max_price', 8000):,} 通知", "size": "xs", "color": "#D32F2F", "weight": "bold", "align": "end", "flex": 5},
                    ],
                }
            )
    else:
        route_items.append(
            {"type": "text", "text": "尚未設定特定航線（可輸入『訂閱 東京 6500』快速新增）", "size": "xs", "color": "#757575", "wrap": True}
        )

    bug_on = "🟢 已開啟秒殺推播" if sub.get("bug_fare_alert", True) else "⚪ 未開啟"
    clr_on = "🟢 已開啟晚鳥通知" if sub.get("clearance_alert", True) else "⚪ 未開啟"

    return {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": "#283593",
            "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "🔔 個人化降價與 Bug 價訂閱雷達", "color": "#C5CAE9", "size": "xs", "weight": "bold"},
                {"type": "text", "text": "我的航線目標價與推播設定", "color": "#FFFFFF", "size": "lg", "weight": "bold", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "14px",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "🔥 全網 Bug 價警報", "size": "xs", "color": "#424242", "flex": 5},
                        {"type": "text", "text": bug_on, "size": "xs", "weight": "bold", "color": "#2E7D32", "align": "end", "flex": 5},
                    ],
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "⚡ 14天內清艙計畫票", "size": "xs", "color": "#424242", "flex": 5},
                        {"type": "text", "text": clr_on, "size": "xs", "weight": "bold", "color": "#2E7D32", "align": "end", "flex": 5},
                    ],
                },
                {"type": "separator", "margin": "sm"},
                {"type": "text", "text": "🎯 監控中的目標航線與預算上限：", "size": "xs", "weight": "bold", "color": "#1A237E", "margin": "xs"},
                *route_items,
                {"type": "separator", "margin": "sm"},
                {
                    "type": "text",
                    "text": "💡 快捷指令：直接輸入「訂閱 東京 6000」、「訂閱 沖繩 4000」或「取消訂閱 東京」即可秒速更新！",
                    "size": "xxs",
                    "color": "#616161",
                    "wrap": True,
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "xs",
            "paddingAll": "12px",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "color": "#283593",
                    "action": {
                        "type": "uri",
                        "label": "🎛️ 開啟 LIFF 雷達面板調整預算",
                        "uri": clean_uri(liff_url),
                    },
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": "🔥 立即查看符合我預算的神價",
                        "text": "Bug價雷達",
                    },
                },
            ],
        },
    }
