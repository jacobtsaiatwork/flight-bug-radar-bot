"""
三大機票情報引擎 (Radar Engine)
1. 🔥 Bug 價與破盤促銷雷達 (致敬豬隊友 Scott / 布萊 N 機票達人風格)
2. ⚡ 旅行社清艙計畫票 / 晚鳥神秘票 (五福、雄獅、可樂、易遊網 14 天內出發)
3. 🔍 Skyscanner 風格跨航司航線比價與廉航含行李真實總價試算 (防範廉航隱藏費用陷阱)
"""

from typing import List, Dict, Any, Optional

# 目的地關鍵字映射表
DESTINATION_ALIASES = {
    "NRT": ["東京", "成田", "羽田", "tokyo", "nrt", "hnd", "日本東京"],
    "KIX": ["大阪", "關西", "京都", "osaka", "kix", "京阪"],
    "OKA": ["沖繩", "那霸", "okinawa", "oka", "琉球"],
    "ICN": ["首爾", "仁川", "金浦", "韓國", "seoul", "icn", "gmp"],
    "BKK": ["曼谷", "泰國", "蘇凡納布", "廊曼", "bangkok", "bkk", "dmk"],
    "EUR": ["歐洲", "巴黎", "倫敦", "米蘭", "羅馬", "法蘭克福", "維也納", "阿姆斯特丹", "europe", "cdg", "lhr", "mxp", "vie"],
    "CTS": ["北海道", "札幌", "新千歲", "sapporo", "cts"],
    "FUK": ["福岡", "九州", "fukuoka", "fuk"],
}

# 1. 🔥 Bug 價與破盤促銷情報資料庫
BUG_AND_PROMO_DEALS: List[Dict[str, Any]] = [
    {
        "deal_id": "BUG-CX-NRT-01",
        "category": "bug_fare",
        "airline": "國泰航空 Cathay Pacific",
        "airline_code": "CX",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "NRT",
        "dest_name": "東京成田",
        "city": "東京",
        "flight_no_out": "CX450",
        "flight_no_in": "CX451",
        "dep_time_out": "13:00",
        "arr_time_out": "17:10",
        "dep_time_in": "15:40",
        "arr_time_in": "18:35",
        "flight_slot_type": "午去午回黃金時段",
        "days": 5,
        "cabin": "經濟艙 (Q艙)",
        "total_price_tax_included": 6850,
        "historical_avg_price": 15200,
        "baggage_included": True,
        "baggage_detail": "含 23kg×2 件托運 + 7kg 手提 + 飛機餐",
        "travel_period": "2026/11/10 - 2027/03/25 (排除農曆春節)",
        "countdown_note": "⏰ 隨時改回原價！外站匯率與稅金溢算 Bug",
        "expert_comment": "🎙️ 達人短評：傳航含兩件 23kg 行李竟然比廉航不買行李還便宜！平均省下 NT$8,350，建議直接刷卡鎖票，出票後請勿致電航司客服！",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/tyoa/",
    },
    {
        "deal_id": "BUG-BR-CDG-02",
        "category": "bug_fare",
        "airline": "長榮航空 EVA Air",
        "airline_code": "BR",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "EUR",
        "dest_name": "巴黎戴高樂",
        "city": "歐洲",
        "flight_no_out": "BR87",
        "flight_no_in": "BR88",
        "dep_time_out": "23:30",
        "arr_time_out": "07:35+1",
        "dep_time_in": "11:20",
        "arr_time_in": "07:00+1",
        "flight_slot_type": "直飛紅眼早到班機",
        "days": 8,
        "cabin": "豪華經濟艙 / 經濟艙",
        "total_price_tax_included": 14900,
        "historical_avg_price": 36800,
        "baggage_included": True,
        "baggage_detail": "含 23kg×2 件托運 + 直飛不轉機",
        "travel_period": "2026/11/15 - 2027/02/28",
        "countdown_note": "🔥 史詩級燃油附加費漏掛 Bug！剩餘極少票池",
        "expert_comment": "🎙️ 達人短評：直飛巴黎來回含稅不到 1 萬 5！正常直飛要 3 萬 6 以上，整整打 4 折！請先拿到電子機票號碼 (13碼) 後過 48 小時再訂不可退飯店。",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/cdg/",
    },
    {
        "deal_id": "PROMO-JX-KIX-03",
        "category": "promo",
        "airline": "星宇航空 STARLUX",
        "airline_code": "JX",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "KIX",
        "dest_name": "大阪關西",
        "city": "大阪",
        "flight_no_out": "JX820",
        "flight_no_in": "JX821",
        "dep_time_out": "08:30",
        "arr_time_out": "12:05",
        "dep_time_in": "13:15",
        "arr_time_in": "15:30",
        "flight_slot_type": "早去午回極品航班",
        "days": 5,
        "cabin": "經濟艙限量促銷",
        "total_price_tax_included": 9680,
        "historical_avg_price": 15800,
        "baggage_included": True,
        "baggage_detail": "含 23kg 托運 + 胡同燒肉機上餐 + 免費機上 Wi-Fi",
        "travel_period": "2026/11/05 - 2027/01/20",
        "countdown_note": "⚡ 旅展破盤快閃！倒數 18 小時結尾",
        "expert_comment": "🎙️ 達人短評：星宇大阪線萬年難得跌破萬元大關！而且是早去午回 A350 廣體機執飛，第一天中午前就能到道頓堀吃一蘭拉麵！",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/kix/",
    },
    {
        "deal_id": "PROMO-MM-OKA-04",
        "category": "promo",
        "airline": "樂桃航空 Peach",
        "airline_code": "MM",
        "is_lcc": True,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "OKA",
        "dest_name": "沖繩那霸",
        "city": "沖繩",
        "flight_no_out": "MM922",
        "flight_no_in": "MM927",
        "dep_time_out": "09:35",
        "arr_time_out": "12:15",
        "dep_time_in": "16:45",
        "arr_time_in": "17:30",
        "flight_slot_type": "早去晚回滿檔班機",
        "days": 4,
        "cabin": "Minimum 促銷票",
        "total_price_tax_included": 3480,
        "historical_avg_price": 7600,
        "baggage_included": False,
        "baggage_detail": "含 7kg 手提 (加購 20kg 來回托運約 +NT$1,800)",
        "travel_period": "2026/11/01 - 2026/12/20",
        "countdown_note": "🔥 72 小時季末閃促！比高鐵台北左營來回還划算",
        "expert_comment": "🎙️ 達人短評：沖繩來回含稅 NT$3,480！就算兩個人合買一件 20kg 托運行李攤提下來一人也才 4,380 元，週末請兩天假直接去美麗海水族館看鯨鯊！",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/oka/",
    },
    {
        "deal_id": "BUG-TG-BKK-05",
        "category": "bug_fare",
        "airline": "泰國國際航空 Thai Airways",
        "airline_code": "TG",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "BKK",
        "dest_name": "曼谷蘇凡納布",
        "city": "曼谷",
        "flight_no_out": "TG633",
        "flight_no_in": "TG632",
        "dep_time_out": "14:05",
        "arr_time_out": "16:50",
        "dep_time_in": "08:25",
        "arr_time_in": "13:05",
        "flight_slot_type": "午去早回舒適航班",
        "days": 5,
        "cabin": "經濟艙特惠",
        "total_price_tax_included": 5490,
        "historical_avg_price": 10800,
        "baggage_included": True,
        "baggage_detail": "含 23kg 托運行李 + 泰式熱餐飲品",
        "travel_period": "2026/11/01 - 2027/03/15",
        "countdown_note": "🔥 泰航 OTA 聯名票價系統折價券疊加神價",
        "expert_comment": "🎙️ 達人短評：曼谷免簽延長加上泰航傳航含稅 5,490 元！比越捷或泰獅航加完行李還便宜 1,500 元，直接升等傳統航空享受大空間！",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/bkk/",
    },
    {
        "deal_id": "PROMO-KE-ICN-06",
        "category": "promo",
        "airline": "大韓航空 Korean Air",
        "airline_code": "KE",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "ICN",
        "dest_name": "首爾仁川",
        "city": "首爾",
        "flight_no_out": "KE186",
        "flight_no_in": "KE185",
        "dep_time_out": "12:25",
        "arr_time_out": "16:00",
        "dep_time_in": "09:00",
        "arr_time_in": "11:00",
        "flight_slot_type": "午去早回傳統航空",
        "days": 4,
        "cabin": "經濟艙特價",
        "total_price_tax_included": 6200,
        "historical_avg_price": 11200,
        "baggage_included": True,
        "baggage_detail": "含 23kg 托運 + 正宗韓式拌飯飛機餐",
        "travel_period": "2026/11/10 - 2027/02/15",
        "countdown_note": "⚡ 秋冬賞楓滑雪季早鳥破盤！餘票倒數中",
        "expert_comment": "🎙️ 達人短評：去首爾弘大、聖水洞爆買保養品跟冬衣最怕行李超重！大韓航空含 23kg 托運只要 6,200 元，不用在機場狼狽塞行李！",
        "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/icn/",
    },
]

# 2. ⚡ 旅行社清艙計畫票 / 晚鳥神秘票資料庫 (14天內出發)
CLEARANCE_DEALS: List[Dict[str, Any]] = [
    {
        "deal_id": "CLR-LION-NRT-01",
        "category": "clearance",
        "agency": "雄獅旅遊 Lion Travel",
        "airline": "台灣虎航 Tigerair",
        "airline_code": "IT",
        "is_lcc": True,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "NRT",
        "dest_name": "東京成田",
        "city": "東京",
        "flight_no_out": "IT200",
        "flight_no_in": "IT203",
        "dep_time_out": "06:35",
        "arr_time_out": "10:40",
        "dep_time_in": "18:25",
        "arr_time_in": "21:30",
        "flight_slot_type": "紅眼早去晚回玩足5天",
        "days": 5,
        "departure_in_days": 4,
        "travel_period": "4 天後出發 (5天4夜團體清艙計畫票)",
        "seats_left": 3,
        "total_price_tax_included": 5999,
        "historical_avg_price": 12500,
        "baggage_included": True,
        "baggage_detail": "清艙包團特仕：已含 20kg 托運行李 + 10kg 手提 + 虎航機上餐",
        "countdown_note": "🚨 距出發僅剩 4 天！最後 3 席倒貼出清",
        "expert_comment": "🎙️ 達人短評：旅行社包機切位最後 3 張賣不完直接砍半價拋售！雖然是團票不可改期，但已經包好來回 20kg 托運行李而且是早去晚回神時段！",
        "booking_url": "https://www.liontravel.com/category/zh-tw/flight",
    },
    {
        "deal_id": "CLR-COLA-KIX-02",
        "category": "clearance",
        "agency": "可樂旅遊 Cola Tour",
        "airline": "中華航空 China Airlines",
        "airline_code": "CI",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "KIX",
        "dest_name": "大阪關西",
        "city": "大阪",
        "flight_no_out": "CI156",
        "flight_no_in": "CI157",
        "dep_time_out": "08:10",
        "arr_time_out": "11:40",
        "dep_time_in": "12:50",
        "arr_time_in": "15:00",
        "flight_slot_type": "早去午回華航直飛",
        "days": 5,
        "departure_in_days": 6,
        "travel_period": "6 天後出發 (5天4夜計畫機票)",
        "seats_left": 2,
        "total_price_tax_included": 7888,
        "historical_avg_price": 15600,
        "baggage_included": True,
        "baggage_detail": "含 23kg 托運行李 + 7kg 手提 + 華航熱餐",
        "countdown_note": "🚨 最後 2 席清倉！下週一馬上飛關西賞楓",
        "expert_comment": "🎙️ 達人短評：華航大阪早去午回竟然只要 7,888 元含稅！這是可樂旅遊退團釋出的最後 2 張機位，適合說走就走的自由行玩家！",
        "booking_url": "https://www.colatour.com.tw/",
    },
    {
        "deal_id": "CLR-LIFETOUR-OKA-03",
        "category": "clearance",
        "agency": "五福旅遊 Life Tour",
        "airline": "馬印航空 Batik Air",
        "airline_code": "OD",
        "is_lcc": False,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "OKA",
        "dest_name": "沖繩那霸",
        "city": "沖繩",
        "flight_no_out": "OD882",
        "flight_no_in": "OD883",
        "dep_time_out": "13:00",
        "arr_time_out": "15:25",
        "dep_time_in": "16:25",
        "arr_time_in": "17:05",
        "flight_slot_type": "午去晚回不早起航班",
        "days": 4,
        "departure_in_days": 3,
        "travel_period": "3 天後出發 (4天3夜晚鳥清艙)",
        "seats_left": 4,
        "total_price_tax_included": 3999,
        "historical_avg_price": 8800,
        "baggage_included": True,
        "baggage_detail": "含 20kg 托運行李 + 7kg 手提",
        "countdown_note": "⚡ 3 天後起飛！含 20kg 托運跌破四千大關",
        "expert_comment": "🎙️ 達人短評：五福清艙沖繩 4 天 3 夜含 20kg 托運行李只要 3,999 元！時間是舒適的午去晚回，不用半夜去桃園機場睡長椅！",
        "booking_url": "https://www.lifetour.com.tw/",
    },
    {
        "deal_id": "CLR-EZTRAVEL-ICN-04",
        "category": "clearance",
        "agency": "易遊網 ezTravel",
        "airline": "酷航 Scoot (波音787夢幻客機)",
        "airline_code": "TR",
        "is_lcc": True,
        "origin": "TPE",
        "origin_name": "台北桃園",
        "dest": "ICN",
        "dest_name": "首爾仁川",
        "city": "首爾",
        "flight_no_out": "TR896",
        "flight_no_in": "TR897",
        "dep_time_out": "18:10",
        "arr_time_out": "21:35",
        "dep_time_in": "23:00",
        "arr_time_in": "00:45+1",
        "flight_slot_type": "晚去晚回下班直奔機場",
        "days": 4,
        "departure_in_days": 9,
        "travel_period": "9 天後出發 (4天3夜神秘機加酒/純機票清艙)",
        "seats_left": 5,
        "total_price_tax_included": 4680,
        "historical_avg_price": 9500,
        "baggage_included": True,
        "baggage_detail": "清艙專案贈送：來回 20kg 托運行李 + 10kg 手提",
        "countdown_note": "🔥 剩餘 5 席！波音 787 雙走道大飛機含行李",
        "expert_comment": "🎙️ 達人短評：下班後直接去桃園機場搭 18:10 的 787 大飛機去首爾吃宵夜炸雞！回程也是 23:00 起飛玩滿最後一天，還送來回 20kg 托運！",
        "booking_url": "https://flight.eztravel.com.tw/",
    },
]

# 3. 🔍 Skyscanner 風格跨航司航線比價與廉航含行李真實總價試算資料庫
ROUTE_COMPARISON_DB: Dict[str, Dict[str, Any]] = {
    "NRT": {
        "dest_code": "NRT",
        "city": "東京",
        "airport_name": "東京成田/羽田 (NRT/HND)",
        "historical_avg_price": 14800,
        "carriers": [
            {
                "airline": "國泰航空 Cathay Pacific",
                "airline_code": "CX",
                "is_lcc": False,
                "base_fare_tax_included": 6850,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg × 2 件免費托運",
                "flight_time": "13:00-17:10 / 15:40-18:35",
                "deal_id": "BUG-CX-NRT-01",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/tyoa/",
            },
            {
                "airline": "台灣虎航 Tigerair",
                "airline_code": "IT",
                "is_lcc": True,
                "base_fare_tax_included": 5800,
                "baggage_fee_roundtrip": 2200,
                "meal_and_seat_fee": 500,
                "baggage_allowance": "手提 10kg (托運 20kg 需加購 +$2,200)",
                "flight_time": "06:35-10:40 / 18:25-21:30",
                "deal_id": "CLR-LION-NRT-01",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/tyoa/",
            },
            {
                "airline": "樂桃航空 Peach",
                "airline_code": "MM",
                "is_lcc": True,
                "base_fare_tax_included": 6100,
                "baggage_fee_roundtrip": 2000,
                "meal_and_seat_fee": 400,
                "baggage_allowance": "手提 7kg (托運 20kg 需加購 +$2,000)",
                "flight_time": "02:25-06:30 / 22:15-01:15",
                "deal_id": "BUG-CX-NRT-01",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/tyoa/",
            },
            {
                "airline": "星宇航空 STARLUX",
                "airline_code": "JX",
                "is_lcc": False,
                "base_fare_tax_included": 12400,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg × 1 件免費托運 + 精品機上餐",
                "flight_time": "08:30-12:30 / 14:00-16:45",
                "deal_id": "BUG-CX-NRT-01",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/tyoa/",
            },
        ],
    },
    "KIX": {
        "dest_code": "KIX",
        "city": "大阪",
        "airport_name": "大阪關西國際機場 (KIX)",
        "historical_avg_price": 14500,
        "carriers": [
            {
                "airline": "中華航空 (可樂清艙票)",
                "airline_code": "CI",
                "is_lcc": False,
                "base_fare_tax_included": 7888,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg 免費托運 + 機上熱餐",
                "flight_time": "08:10-11:40 / 12:50-15:00",
                "deal_id": "CLR-COLA-KIX-02",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/kix/",
            },
            {
                "airline": "星宇航空 STARLUX",
                "airline_code": "JX",
                "is_lcc": False,
                "base_fare_tax_included": 9680,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg 免費托運 + 胡同燒肉餐",
                "flight_time": "08:30-12:05 / 13:15-15:30",
                "deal_id": "PROMO-JX-KIX-03",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/kix/",
            },
            {
                "airline": "泰越捷航空 Thai VietJet",
                "airline_code": "VZ",
                "is_lcc": True,
                "base_fare_tax_included": 6200,
                "baggage_fee_roundtrip": 2400,
                "meal_and_seat_fee": 500,
                "baggage_allowance": "手提 7kg (托運 20kg 需加購 +$2,400)",
                "flight_time": "07:50-11:25 / 12:25-14:25",
                "deal_id": "PROMO-JX-KIX-03",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/kix/",
            },
        ],
    },
    "OKA": {
        "dest_code": "OKA",
        "city": "沖繩",
        "airport_name": "沖繩那霸國際機場 (OKA)",
        "historical_avg_price": 7800,
        "carriers": [
            {
                "airline": "馬印航空 (五福清艙票)",
                "airline_code": "OD",
                "is_lcc": False,
                "base_fare_tax_included": 3999,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "20kg 免費托運 + 7kg 手提",
                "flight_time": "13:00-15:25 / 16:25-17:05",
                "deal_id": "CLR-LIFETOUR-OKA-03",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/oka/",
            },
            {
                "airline": "樂桃航空 Peach",
                "airline_code": "MM",
                "is_lcc": True,
                "base_fare_tax_included": 3480,
                "baggage_fee_roundtrip": 1800,
                "meal_and_seat_fee": 300,
                "baggage_allowance": "手提 7kg (托運 20kg 需加購 +$1,800)",
                "flight_time": "09:35-12:15 / 16:45-17:30",
                "deal_id": "PROMO-MM-OKA-04",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/oka/",
            },
            {
                "airline": "長榮航空 EVA Air",
                "airline_code": "BR",
                "is_lcc": False,
                "base_fare_tax_included": 7200,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg 免費托運 + 輕食",
                "flight_time": "06:55-09:15 / 10:15-10:55",
                "deal_id": "PROMO-MM-OKA-04",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/oka/",
            },
        ],
    },
    "ICN": {
        "dest_code": "ICN",
        "city": "首爾",
        "airport_name": "首爾仁川國際機場 (ICN)",
        "historical_avg_price": 10800,
        "carriers": [
            {
                "airline": "酷航 Scoot (易遊網清艙含行李)",
                "airline_code": "TR",
                "is_lcc": True,
                "base_fare_tax_included": 4680,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "清艙已贈 20kg 托運 + 10kg 手提",
                "flight_time": "18:10-21:35 / 23:00-00:45",
                "deal_id": "CLR-EZTRAVEL-ICN-04",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/icn/",
            },
            {
                "airline": "大韓航空 Korean Air",
                "airline_code": "KE",
                "is_lcc": False,
                "base_fare_tax_included": 6200,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg 免費托運 + 韓式拌飯餐",
                "flight_time": "12:25-16:00 / 09:00-11:00",
                "deal_id": "PROMO-KE-ICN-06",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/icn/",
            },
            {
                "airline": "濟州航空 Jeju Air",
                "airline_code": "7C",
                "is_lcc": True,
                "base_fare_tax_included": 4500,
                "baggage_fee_roundtrip": 2300,
                "meal_and_seat_fee": 400,
                "baggage_allowance": "手提 10kg (加購 15kg 托運 +$2,300)",
                "flight_time": "02:15-05:50 / 22:30-00:10",
                "deal_id": "PROMO-KE-ICN-06",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/icn/",
            },
        ],
    },
    "BKK": {
        "dest_code": "BKK",
        "city": "曼谷",
        "airport_name": "曼谷蘇凡納布/廊曼 (BKK/DMK)",
        "historical_avg_price": 10500,
        "carriers": [
            {
                "airline": "泰國國際航空 Thai Airways",
                "airline_code": "TG",
                "is_lcc": False,
                "base_fare_tax_included": 5490,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg 免費托運 + 泰式熱餐",
                "flight_time": "14:05-16:50 / 08:25-13:05",
                "deal_id": "BUG-TG-BKK-05",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/bkk/",
            },
            {
                "airline": "泰國亞洲航空 Thai AirAsia",
                "airline_code": "FD",
                "is_lcc": True,
                "base_fare_tax_included": 4850,
                "baggage_fee_roundtrip": 2100,
                "meal_and_seat_fee": 350,
                "baggage_allowance": "手提 7kg (加購 20kg 托運 +$2,100)",
                "flight_time": "13:30-16:20 / 07:25-12:10",
                "deal_id": "BUG-TG-BKK-05",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/bkk/",
            },
        ],
    },
    "EUR": {
        "dest_code": "EUR",
        "city": "歐洲",
        "airport_name": "巴黎戴高樂機場 (CDG)",
        "historical_avg_price": 36800,
        "carriers": [
            {
                "airline": "長榮航空 EVA Air (直飛 Bug 價)",
                "airline_code": "BR",
                "is_lcc": False,
                "base_fare_tax_included": 14900,
                "baggage_fee_roundtrip": 0,
                "meal_and_seat_fee": 0,
                "baggage_allowance": "23kg × 2 件免費托運 + 全程直飛",
                "flight_time": "23:30-07:35+1 / 11:20-07:00+1",
                "deal_id": "BUG-BR-CDG-02",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/cdg/",
            },
            {
                "airline": "酷航 Scoot (經新加坡轉機)",
                "airline_code": "TR",
                "is_lcc": True,
                "base_fare_tax_included": 16500,
                "baggage_fee_roundtrip": 4600,
                "meal_and_seat_fee": 1200,
                "baggage_allowance": "手提 10kg (長途加購 20kg 托運 +$4,600)",
                "flight_time": "轉機 1 次 (總航程 19 小時)",
                "deal_id": "BUG-BR-CDG-02",
                "booking_url": "https://www.skyscanner.com.tw/transport/flights/tpe/cdg/",
            },
        ],
    },
}


class RadarEngine:
    """機票清艙與 Bug 價雷達核心引擎"""

    @staticmethod
    def evaluate_thermometer(current_price: int, historical_avg: int) -> Dict[str, Any]:
        """
        計算「真假特價溫度計」指標
        回傳折數、省下金額、溫度計評級、進度條百分比與顏色
        """
        if historical_avg <= 0:
            historical_avg = max(current_price, 10000)

        saved_amount = max(0, historical_avg - current_price)
        ratio = current_price / historical_avg
        discount_fold = round(ratio * 10, 1)

        if ratio <= 0.48:
            grade = "🔥🔥🔥 史詩級 Bug 價"
            badge_color = "#D32F2F"
            bar_percent = 98
            advice = "閉眼直接刷卡！慢一秒隨時被航司拔插頭改回原價！"
        elif ratio <= 0.62:
            grade = "⚡ 破盤神價 (年度前 5% 低價)"
            badge_color = "#E65100"
            bar_percent = 88
            advice = "遠低於歷史均價！連假或旺季絕對看不到的甜甜價，強烈建議入手！"
        elif ratio <= 0.78:
            grade = "🟢 值得入手好價"
            badge_color = "#2E7D32"
            bar_percent = 72
            advice = "比平時便宜不少，若請假日期剛好對得上可以直接買！"
        else:
            grade = "🟡 一般促銷 (建議觀望)"
            badge_color = "#F57F17"
            bar_percent = 45
            advice = "常見促銷價位，若不急著出國可先設定降價訂閱通知。"

        return {
            "saved_amount": saved_amount,
            "discount_fold": discount_fold,
            "discount_percent": round((1 - ratio) * 100),
            "thermometer_grade": grade,
            "badge_color": badge_color,
            "bar_percent": bar_percent,
            "buying_advice": advice,
        }

    def enrich_deal(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """為單筆機票情報加上溫度計評級與省下金額計算"""
        item = dict(deal)
        thermo = self.evaluate_thermometer(
            item.get("total_price_tax_included", 0),
            item.get("historical_avg_price", 10000),
        )
        item.update(thermo)
        return item

    def get_bug_and_promo_deals(self, dest_filter: Optional[str] = None, max_price: Optional[int] = None) -> List[Dict[str, Any]]:
        """取得 🔥 Bug 價與破盤促銷清單"""
        dest_code = self.resolve_dest_code(dest_filter) if dest_filter else None
        results = []
        for d in BUG_AND_PROMO_DEALS:
            if dest_code and d["dest"] != dest_code:
                continue
            if max_price and d["total_price_tax_included"] > max_price:
                continue
            results.append(self.enrich_deal(d))
        results.sort(key=lambda x: x["total_price_tax_included"])
        return results

    def get_clearance_deals(self, dest_filter: Optional[str] = None, max_days_until_dep: int = 14) -> List[Dict[str, Any]]:
        """取得 ⚡ 旅行社清艙計畫票 / 晚鳥神秘票清單 (預設 14 天內出發)"""
        dest_code = self.resolve_dest_code(dest_filter) if dest_filter else None
        results = []
        for d in CLEARANCE_DEALS:
            if d.get("departure_in_days", 99) > max_days_until_dep:
                continue
            if dest_code and d["dest"] != dest_code:
                continue
            results.append(self.enrich_deal(d))
        results.sort(key=lambda x: (x.get("departure_in_days", 99), x["total_price_tax_included"]))
        return results

    def get_deal_by_id(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """根據 deal_id 查找單筆機票情報 (供一鍵排行程與訂閱使用)"""
        for d in BUG_AND_PROMO_DEALS + CLEARANCE_DEALS:
            if d["deal_id"] == deal_id:
                return self.enrich_deal(d)
        # 若無精確匹配，回傳第一筆預設神價
        if BUG_AND_PROMO_DEALS:
            return self.enrich_deal(BUG_AND_PROMO_DEALS[0])
        return None

    @staticmethod
    def resolve_dest_code(keyword: Optional[str]) -> Optional[str]:
        """將使用者輸入的目的地關鍵字解析為標準代碼 (如 東京 -> NRT)"""
        if not keyword:
            return None
        kw = keyword.strip().lower()
        for code, aliases in DESTINATION_ALIASES.items():
            if kw == code.lower() or any(a in kw or kw in a for a in aliases):
                return code
        return None

    def compare_route_true_cost(self, query: str, include_baggage: bool = True) -> Dict[str, Any]:
        """
        🔍 Skyscanner 風格跨航司航線比價與廉航含行李真實總價試算
        自動計算：票面含稅價 vs 加購 20kg 托運行李與餐選位後的「真實總成本」
        揭露表面便宜但加完行李比傳統航空還貴的「廉航隱藏費用陷阱」！
        """
        code = self.resolve_dest_code(query) or "NRT"
        route_info = ROUTE_COMPARISON_DB.get(code, ROUTE_COMPARISON_DB["NRT"])

        compared_carriers = []
        for c in route_info["carriers"]:
            base_price = c["base_fare_tax_included"]
            bag_fee = c["baggage_fee_roundtrip"] if include_baggage else 0
            true_total = base_price + bag_fee
            thermo = self.evaluate_thermometer(true_total, route_info["historical_avg_price"])

            carrier_entry = {
                **c,
                "true_total_with_baggage": true_total,
                "hidden_fee_ratio": round((bag_fee / true_total) * 100) if true_total > 0 else 0,
                "is_lcc_trap": False,
                **thermo,
            }
            compared_carriers.append(carrier_entry)

        # 依含行李真實總價由低到高排序
        compared_carriers.sort(key=lambda x: x["true_total_with_baggage"])

        # 找出最便宜的傳統航空含行李真實價格，標記表面便宜但加完行李比傳航貴的廉航陷阱
        fsc_prices = [c["true_total_with_baggage"] for c in compared_carriers if not c["is_lcc"]]
        min_fsc_price = min(fsc_prices) if fsc_prices else None

        for c in compared_carriers:
            if c["is_lcc"] and min_fsc_price is not None:
                if c["base_fare_tax_included"] < min_fsc_price and c["true_total_with_baggage"] >= min_fsc_price:
                    c["is_lcc_trap"] = True

        best_choice = compared_carriers[0] if compared_carriers else None

        return {
            "dest_code": route_info["dest_code"],
            "city": route_info["city"],
            "airport_name": route_info["airport_name"],
            "historical_avg_price": route_info["historical_avg_price"],
            "best_choice": best_choice,
            "carriers": compared_carriers,
            "trap_warning": (
                f"💡 雷達防坑提醒：{route_info['city']}線目前傳統航空含行李最低僅 NT${min_fsc_price:,}，部分廉航表面未加行李看似便宜，加購來回 20kg 托運後反而貴上 NT${max(0, max(c['true_total_with_baggage'] for c in compared_carriers) - min_fsc_price):,}！"
                if min_fsc_price
                else "💡 已為您自動納入來回 20kg 托運行李試算真實總成本！"
            ),
        }

    def get_everywhere_cheapest_ranking(self) -> List[Dict[str, Any]]:
        """🌍 飛哪裡最便宜：全航線最低含稅總價排行榜"""
        all_deals = [self.enrich_deal(d) for d in BUG_AND_PROMO_DEALS + CLEARANCE_DEALS]
        best_by_city: Dict[str, Dict[str, Any]] = {}
        for d in all_deals:
            city = d["city"]
            if city not in best_by_city or d["total_price_tax_included"] < best_by_city[city]["total_price_tax_included"]:
                best_by_city[city] = d
        ranked = list(best_by_city.values())
        ranked.sort(key=lambda x: x["total_price_tax_included"])
        return ranked


radar_engine = RadarEngine()
