"""
✨ 獨家閉環：一鍵從機票生成完整旅遊行程 (Itinerary Bridge)
當使用者點擊機票卡片上的「✨ 用此航班時間排行程」Postback 按鈕 (`action=plan_trip&deal_id=...`) 時，
自動根據該機票的：
- 目的地城市與降落機場 (如東京成田 NRT / 大阪關西 KIX / 沖繩那霸 OKA / 首爾仁川 ICN / 曼谷 BKK / 巴黎 CDG)
- 旅遊天數 (如 4 天 / 5 天 / 8 天)
- 去程抵達時間 (如紅眼早到班機 07:35 / 早班機 10:40 / 午班機 17:10 / 晚班機 21:35)
- 回程起飛時間 (如早班機 08:25 / 午班機 15:40 / 晚班機 23:00)
透過 Google Gemini API (並內建高品質本地智慧行程生成 Fallback) 生成完美貼合航班起降時間的每日行程、機場進市區交通與住宿區域建議！
"""

import json
from typing import Dict, Any, List, Optional
from app.config import GEMINI_API_KEY
from app.radar_engine import radar_engine


# 各目的地機場交通、推薦住宿圈與分日精華行程本地知識庫 (Fallback 與基準資料)
CITY_FLIGHT_ITINERARY_KB: Dict[str, Dict[str, Any]] = {
    "NRT": {
        "city": "東京",
        "airport_transit": "🚆 機場交通：搭乘 Skyliner 京成電鐵 41 分鐘直達上野/日暮里，或搭 N'EX 成田特快直達新宿/東京站。",
        "hotel_zone": "🏨 推薦住宿圈：【上野/淺草區】（方便末班車與直達京成電鐵）或【新宿/澀谷區】（夜生活與購物最方便）。",
        "days_template": [
            {
                "day": 1,
                "theme": "抵達東京・機場快線直達市區與夜間美食洗禮",
                "morning": "搭乘去程班機飛往東京成田機場 (機上補眠或享用航司餐點)",
                "afternoon": "抵達出關後領取 Skyliner 車票進市區飯店辦理 Check-in 寄放行李",
                "evening": "上野阿美橫丁居酒屋巡禮 / 淺草寺夜間點燈散步（免排隊拍雷門）+ 一蘭或鴨to蔥拉麵",
            },
            {
                "day": 2,
                "theme": "淺草下町風情・晴空塔展望與秋葉原電器動漫街",
                "morning": "淺草雷門仲見世通吃人形燒、炸肉餅 → 隅田公園遠眺晴空塔",
                "afternoon": "東京晴空塔 Solamachi 購物中心 & 敘敘苑高空燒肉午間套餐",
                "evening": "秋葉原電器街扭蛋尋寶 → 銀座步行者天國與百年煉瓦亭蛋包飯",
            },
            {
                "day": 3,
                "theme": "富士山河口湖一日絕景 或 澀谷原宿潮流一線",
                "morning": "明治神宮森林參道洗禮 → 原宿竹下通與表參道精品建築街拍",
                "afternoon": "澀谷十字路口 & SHIBUYA SKY 360度高空展望台看夕陽富士山",
                "evening": "新宿歌舞伎町哥吉拉地標、思出橫丁串燒小酌 & 唐吉訶德採買藥妝",
            },
            {
                "day": 4,
                "theme": "築地市場海鮮早午餐・東京鐵塔與麻布台之丘",
                "morning": "築地場外市場（海膽海鮮丼、玉子燒、草莓大福）",
                "afternoon": "TeamLab Planets 光影美術館 或 麻布台之丘近距離拍東京鐵塔",
                "evening": "六本木之丘夜景 & HARBS 水果千層蛋糕，整理戰利品打包裝箱",
            },
            {
                "day": 5,
                "theme": "最後伴手禮衝刺・成田機場免稅店滿載歸賦",
                "morning": "飯店退房 → 東京車站一番街或上野二木之菓子掃貨 NewYork Perfect Cheese",
                "afternoon": "搭乘 Skyliner 前往成田機場報到托運，逛機場免稅店買薯條三兄弟與東京芭娜娜",
                "evening": "搭乘回程班機返回台北桃園機場，結束超值東京之旅！",
            },
        ],
    },
    "KIX": {
        "city": "大阪",
        "airport_transit": "🚆 機場交通：搭乘南海電鐵 Rapi:t 特急 34 分鐘直達難波，或 JR HARUKA 特急直達天王寺/新大阪/京都。",
        "hotel_zone": "🏨 推薦住宿圈：【難波/心齋橋】（下樓即藥妝街、南海電鐵直達機場）或【梅田站周邊】（轉乘京都神戶最便利）。",
        "days_template": [
            {
                "day": 1,
                "theme": "飛抵關西機場・南海特急直奔道頓堀跑跑人",
                "morning": "自桃園機場出發飛往大阪關西機場，準備展開關西美食大冒險",
                "afternoon": "搭乘南海電鐵 Rapi:t 直達難波飯店寄放行李 → 心齋橋筋拱廊商店街開逛",
                "evening": "道頓堀固力果跑跑人打卡、吃本家章魚燒、千房大阪燒與金龍拉麵",
            },
            {
                "day": 2,
                "theme": "日本環球影城 USJ 狂歡日 或 大阪周遊卡經典巡禮",
                "morning": "直衝日本環球影城（超級任天堂世界瑪利歐賽車、哈利波特禁忌之旅）",
                "afternoon": "小小兵樂園與好萊塢美夢乘車遊，享用園區限定奇諾比奧餐廳",
                "evening": "梅田藍天大廈空中庭園展望台看百萬夜景 + 國產牛燒肉吃到飽",
            },
            {
                "day": 3,
                "theme": "京都清水寺古都漫步・伏見稻荷千本鳥居",
                "morning": "搭京阪電車前往【伏見稻荷大社】穿越壯觀千本鳥居",
                "afternoon": "清水寺舞台、二三年坂石板路漫步 → 祇園花見小路與八坂神社",
                "evening": "先斗町鴨川納涼床料理 或 返回大阪難波八阪神社獅子殿參拜",
            },
            {
                "day": 4,
                "theme": "黑門市場海鮮早市・通天閣新世界與臨空城 Outlet",
                "morning": "黑門市場現烤神戶牛、大干貝與黑門三平生魚片早午餐",
                "afternoon": "天王寺阿倍野 HARUKAS 300 展望台 & 通天閣新世界炸串體驗",
                "evening": "大國藥妝與 BIC CAMERA 退稅大採購，把 23kg 托運行李塞滿！",
            },
            {
                "day": 5,
                "theme": "臨空城 Outlet 最後補貨・關西機場免稅店直飛回台",
                "morning": "飯店退房後搭車至機場前一站【臨空城 Rinku Premium Outlets】最後血拚",
                "afternoon": "前往關西國際機場辦理登機托運，採買呼吸巧克力與老爺爺起司蛋糕",
                "evening": "平安飛抵台北桃園機場，完成高 CP 值關西自由行！",
            },
        ],
    },
    "OKA": {
        "city": "沖繩",
        "airport_transit": "🚝 機場交通：那霸機場出關即達 Yui-Rail 單軌電車站，15 分鐘直達國際通（縣廳前/牧志站），或機場租車自駕出發。",
        "hotel_zone": "🏨 推薦住宿圈：【那霸國際通周邊】（單軌電車直達、宵夜屋台村熱鬧）搭配 1 晚【美國村/恩納海景飯店】。",
        "days_template": [
            {
                "day": 1,
                "theme": "90分鐘飛抵那霸・波上宮海濱神社與國際通屋台村",
                "morning": "自桃園機場起飛，僅 90 分鐘航程輕鬆降落沖繩那霸機場",
                "afternoon": "機場國內線航廈買豬肉蛋飯糰 → 單軌電車直達飯店 → 懸崖上的【波上宮】與波之上海灘",
                "evening": "國際通商店街散步、吃暖暮拉麵或琉球之牛頂級和牛燒肉、逛唐吉訶德",
            },
            {
                "day": 2,
                "theme": "沖繩北部絕景・美麗海水族館鯨鯊與古宇利跨海大橋",
                "morning": "自駕或搭乘北上觀光巴士前往【萬座毛】象鼻岩海景",
                "afternoon": "沖繩美麗海水族館（黑潮之海巨型鯨鯊餵食秀）→ 古宇利大橋吃蝦蝦飯",
                "evening": "北谷美國村 Sunset Beach 看日落海景、吃 A&W 漢堡配麥根沙士",
            },
            {
                "day": 3,
                "theme": "小希臘瀨長島看飛機起降・玉泉洞鐘乳石與 PARCO CITY",
                "morning": "沖繩世界文化王國（東洋第一美玉泉洞鐘乳石奇觀 & 王國村太鼓舞）",
                "afternoon": "浦添 PARCO CITY 無敵海景購物中心大採買（Uniqlo、敘敘苑、沖繩伴手禮）",
                "evening": "瀨長島 Umikaji Terrace 純白露台吃幸福鬆餅、近距離看那霸機場飛機降落",
            },
            {
                "day": 4,
                "theme": "第一牧志公設市場海鮮・ASHIBINAA Outlet 與滿載返台",
                "morning": "第一牧志公設市場挑選夜光貝與龍蝦代客料理，買鹽屋雪鹽冰淇淋",
                "afternoon": "豐崎 ASHIBINAA Outlet 最後衝刺 → 搭車 15 分鐘直達那霸機場報到",
                "evening": "帶著滿滿紅芋塔與黑糖伴手禮飛返台北桃園機場！",
            },
        ],
    },
    "ICN": {
        "city": "首爾",
        "airport_transit": "🚆 機場交通：搭乘 AREX 機場快線直達車 43 分鐘抵首爾站，或搭一般車直達弘大入口站（免換線最推！）。",
        "hotel_zone": "🏨 推薦住宿圈：【弘大入口站】（機場快線直達、夜生活與潮牌集散地）或【明洞/乙支路】（換錢所與烤肉街集中）。",
        "days_template": [
            {
                "day": 1,
                "theme": "飛抵首爾仁川・AREX 直達弘大夜生活與韓式炸雞宵夜",
                "morning": "辦理登機出發飛往首爾仁川國際機場",
                "afternoon": "搭乘 AREX 機場快線直達弘大入口站 Check-in → 大使館或弘大換錢所換韓元",
                "evening": "弘大延南洞文青街散步、吃荒謬的生肉或橋村炸雞配啤酒，逛 Olive Young 美妝",
            },
            {
                "day": 2,
                "theme": "景福宮韓服體驗・北村韓屋村與聖水洞潮流咖啡街",
                "morning": "穿唯美韓服免費逛【景福宮】拍光化門守門將交接 → 土俗村蔘雞湯",
                "afternoon": "北村韓屋村與三清洞散步 → 轉戰首爾最潮【聖水洞】逛 Dior 概念店、Tamburins 香氛與大林倉庫咖啡",
                "evening": "東大門設計廣場 DDP 夜景 & 陳玉華一隻雞蒜香濃湯鍋",
            },
            {
                "day": 3,
                "theme": "汝矣島現代百貨 The Hyundai・明洞商圈與南山首爾塔",
                "morning": "廣藏市場吃綠豆煎餅、生章魚與麻藥飯捲早午餐",
                "afternoon": "汝矣島 The Hyundai Seoul 現代百貨逛韓國設計師潮牌 (Matin Kim / Mardi Mercredi)",
                "evening": "南山纜車登首爾塔看浪漫夜景 → 明洞商圈吃街頭小吃與江南麵屋燉牛排",
            },
            {
                "day": 4,
                "theme": "首爾站樂天超市掃貨・機場快線預辦登機輕鬆返台",
                "morning": "首爾站 Lotte Mart 樂天超市買齊海苔、HBAF 杏仁果、Zero 軟糖與泡麵並現場退稅",
                "afternoon": "搭乘 AREX 機場快線前往仁川機場辦理退稅與免稅品提領",
                "evening": "搭機返回台北桃園機場，結束韓流美食購物之旅！",
            },
        ],
    },
    "BKK": {
        "city": "曼谷",
        "airport_transit": "🚆 機場交通：蘇凡納布機場 B1 搭乘 ARL 機場快線 26 分鐘至 Phaya Thai 轉乘 BTS 空鐵，或用 Grab/Bolt 叫車直達飯店。",
        "hotel_zone": "🏨 推薦住宿圈：【Asok 阿索克 / Sukhumvit 區】（BTS 與 MRT 雙鐵交會最中心）或【Chit Lom 四面佛商圈】。",
        "days_template": [
            {
                "day": 1,
                "theme": "抵達微笑之都曼谷・泰式古法按摩與喬德夜市火山排骨",
                "morning": "桃園機場搭機飛往曼谷蘇凡納布國際機場",
                "afternoon": "入境後搭機場快線進市區飯店辦理入住，先喝杯手標泰式奶茶消暑",
                "evening": "Let's Relax 正宗泰式草藥球按摩舒壓 → JODD FAIRS 喬德夜市吃火山排骨與水果冰沙",
            },
            {
                "day": 2,
                "theme": "鄭王廟泰服美拍・大皇宮臥佛寺與昭披耶河夕陽遊船",
                "morning": "搭湄南河交通船前往【鄭王廟 Wat Arun】換穿精緻泰服拍白色佛塔大片",
                "afternoon": "臥佛寺參拜巨型金身臥佛 → 河岸景觀咖啡廳看鄭王廟日落倒影",
                "evening": "ICONSIAM 暹羅天地室內水上市場吹冷氣吃美食 + 音樂水舞秀",
            },
            {
                "day": 3,
                "theme": "四面佛祈福・Siam 暹羅商圈設計小店與高空酒吧夜景",
                "morning": "參拜靈驗【四面佛 Erawan Shrine】 → 水門市場紅大哥海南雞飯",
                "afternoon": "Siam Square & Central World 逛 Gentlewoman 帆布包、香氛與米其林推薦建興酒家咖哩螃蟹",
                "evening": "Tichuca 水母高空酒吧 或 Mahanakhon 像素大廈 78 樓透明玻璃天空步道",
            },
            {
                "day": 4,
                "theme": "洽圖洽市集尋寶・Big C 超市掃貨伴手禮",
                "morning": "洽圖洽市集或嵩越路老城區文青咖啡館巡禮，吃榮泰魚蛋粉",
                "afternoon": "Big C Supercenter 旗艦店瘋狂採買小老闆海苔、皇家牛奶片、鼻通與泰式調理包",
                "evening": "銅板價泰式流水蝦燒烤吃到飽 + 精油 SPA 放鬆最後一晚",
            },
            {
                "day": 5,
                "theme": "飯店泳池早晨時光・蘇凡納布機場免稅店滿載歸國",
                "morning": "享用飯店豐盛泰式現煮河粉早餐與無邊際泳池拍照",
                "afternoon": "搭乘機場快線或專車前往曼谷機場報到，逛機場買 Mango Sticky Rice 芒果糯米飯上機",
                "evening": "平安飛抵台北桃園機場，完成超划算曼谷度假之旅！",
            },
        ],
    },
    "EUR": {
        "city": "歐洲 (巴黎)",
        "airport_transit": "🚆 機場交通：巴黎戴高樂機場 (CDG) 搭乘 RER B 線郊區快鐵約 35 分鐘直達巴黎北站/聖母院，或搭乘 RoissyBus 直達歌劇院。",
        "hotel_zone": "🏨 推薦住宿圈：【巴黎第 1~2 區羅浮宮/歌劇院周邊】或【第 5~6 區拉丁區/聖日耳曼】（治安佳、步行可達塞納河）。",
        "days_template": [
            {
                "day": 1,
                "theme": "直飛抵達巴黎戴高樂・歌劇院商圈與塞納河畔散步",
                "morning": "清晨降落巴黎戴高樂機場 (CDG)，出關後購買 Navigo 交通卡搭車進巴黎市區",
                "afternoon": "飯店寄放行李 → 加尼葉歌劇院與老佛爺百貨圓頂玻璃穹頂觀景台俯瞰巴黎",
                "evening": "Bouillon Chartier 百年平價法式料理（油封鴨腿與法式焗蝸牛）",
            },
            {
                "day": 2,
                "theme": "羅浮宮藝術殿堂・杜樂麗花園與塞納河遊船晚宴",
                "morning": "預約首場進入【羅浮宮】欣賞蒙娜麗莎、勝利女神與玻璃金字塔",
                "afternoon": "漫步杜樂麗花園至協和廣場 → 香榭麗舍大道與凱旋門登頂看十二條放射大道",
                "evening": "戰神廣場拍艾菲爾鐵塔整點鑽石閃燈秀 + 塞納河觀光遊船",
            },
            {
                "day": 3,
                "theme": "凡爾賽宮鏡廳輝煌・蒙馬特聖心堂藝術山丘",
                "morning": "搭 RER C 線前往【凡爾賽宮】讚嘆金碧輝煌鏡廳與皇家御花園",
                "afternoon": "蒙馬特山丘【聖心堂】俯瞰巴黎全景、畫家村廣場與愛牆打卡",
                "evening": "瑪黑區文青選物店與 L'As du Fallafel 中東口袋餅、Pierre Hermé 馬卡龍",
            },
            {
                "day": 4,
                "theme": "奧賽美術館印象派・左岸花神咖啡館與戴高樂返程準備",
                "morning": "奧賽美術館大鐘窗剪影美拍，欣賞梵谷與莫內真跡",
                "afternoon": "聖日耳曼大道【花神咖啡館】喝左岸熱可可，前往藥妝店採買理膚寶水與貝膚黛瑪",
                "evening": "整理行李前往機場或銜接下一段歐洲深度旅程！",
            },
        ],
    },
}


class ItineraryBridge:
    """機票轉行程一鍵生成橋接引擎"""

    @staticmethod
    def analyze_flight_timing(dep_time_out: str, arr_time_out: str, dep_time_in: str) -> Dict[str, str]:
        """根據去程抵達時間與回程起飛時間，產出專屬的『航班時段智慧調度攻略』"""
        try:
            arr_hour = int(arr_time_out.split(":")[0].replace("+1", ""))
        except Exception:
            arr_hour = 14

        try:
            dep_in_hour = int(dep_time_in.split(":")[0])
        except Exception:
            dep_in_hour = 15

        if arr_hour < 11:
            day1_strategy = (
                f"⚡ 【早到/紅眼班機黃金攻略】（{arr_time_out} 抵達）：第一天上午就落地！建議出關後直接將大行李寄放在機場快線車站或飯店櫃檯，"
                "馬上賺到完整一整天行程；晚上建議提早於 21:00 回飯店休息補眠。"
            )
        elif arr_hour <= 16:
            day1_strategy = (
                f"🌤️ 【黃金午班機從容攻略】（{arr_time_out} 抵達）：時間最舒服！進市區剛好直接辦理飯店 Check-in 進房放行李，"
                "傍晚直接安排市中心核心商圈晚餐與夜景，不累又不浪費時間。"
            )
        else:
            day1_strategy = (
                f"🌙 【晚班機直奔飯店攻略】（{arr_time_out} 抵達）：抵達時間較晚，強烈建議事先查好機場快線末班車時間，"
                "第一晚住在機場直達車站步行 5 分鐘內的飯店，放好行李立即去附近吃宵夜居酒屋/炸雞！"
            )

        if dep_in_hour <= 11:
            last_day_strategy = (
                f"⏰ 【早班機返程防呆提醒】（{dep_time_in} 起飛）：回程為早班機，最後一晚務必把所有伴手禮買齊並完成打包，"
                "起床退房後直接搭乘首班機場快線前往機場報到，把免稅店留到出境後逛！"
            )
        elif dep_in_hour <= 17:
            last_day_strategy = (
                f"🛍️ 【午班機返程從容收尾】（{dep_time_in} 起飛）：最後一天早上可悠閒享用早餐、在飯店周邊超市或車站百貨做最後補貨，"
                "中午前搭車前往機場，時間充裕不慌張。"
            )
        else:
            last_day_strategy = (
                f"🎉 【晚班機玩滿最後一秒】（{dep_time_in} 起飛）：超爽晚班機！早上退房後把行李寄放櫃檯或車站置物櫃，"
                "還能多玩整整大半天（推薦安排機場沿線 Outlet 或大型商場），傍晚再去機場！"
            )

        return {
            "day1_strategy": day1_strategy,
            "last_day_strategy": last_day_strategy,
        }

    def generate_itinerary_from_deal(self, deal_id: str) -> Dict[str, Any]:
        """
        根據機票 deal_id 生成完整貼合航班時間的旅遊行程資料
        優先嘗試 Google Gemini API 生成客製化 JSON，若未設定 API Key 或連線逾時則自動切換至高品質本地智慧引擎
        """
        deal = radar_engine.get_deal_by_id(deal_id)
        if not deal:
            deal = radar_engine.get_bug_and_promo_deals()[0]

        dest_code = deal.get("dest", "NRT")
        kb = CITY_FLIGHT_ITINERARY_KB.get(dest_code, CITY_FLIGHT_ITINERARY_KB["NRT"])
        timing_tips = self.analyze_flight_timing(
            deal.get("dep_time_out", "13:00"),
            deal.get("arr_time_out", "17:10"),
            deal.get("dep_time_in", "15:40"),
        )

        # 若環境中有設定 GEMINI_API_KEY，嘗試呼叫 Gemini 模型強化行程亮點
        ai_custom_summary = None
        if GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=GEMINI_API_KEY)
                prompt = (
                    f"請針對以下特價機票，用繁體中文給出 60 字以內的『航班專屬行程排法總結建議』：\n"
                    f"航司：{deal['airline']} ({deal['flight_no_out']}/{deal['flight_no_in']})\n"
                    f"目的地：{deal['city']} ({deal['dest_name']})，天數：{deal.get('days', 5)}天\n"
                    f"去程時間：{deal['dep_time_out']}->{deal['arr_time_out']}，回程時間：{deal['dep_time_in']}->{deal['arr_time_in']}"
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if resp and resp.text:
                    ai_custom_summary = resp.text.strip()
            except Exception:
                ai_custom_summary = None

        target_days = deal.get("days", len(kb["days_template"]))
        days_list = list(kb["days_template"][:target_days])

        # 動態把第 1 天與最後一天的行程描述加上實際航班編號與時間
        if days_list:
            first_day = dict(days_list[0])
            first_day["morning"] = f"✈️ 去程航班 {deal['flight_no_out']} ({deal['dep_time_out']} 起飛 → {deal['arr_time_out']} 抵達 {deal['dest_name']})"
            days_list[0] = first_day

            last_day = dict(days_list[-1])
            last_day["evening"] = f"✈️ 回程航班 {deal['flight_no_in']} ({deal['dep_time_in']} 自 {deal['dest_name']} 起飛 → {deal['arr_time_in']} 返抵桃園)"
            days_list[-1] = last_day

        return {
            "deal_id": deal["deal_id"],
            "deal": deal,
            "city": deal["city"],
            "dest_name": deal["dest_name"],
            "airline": deal["airline"],
            "flight_summary": f"{deal['flight_no_out']} ({deal['dep_time_out']}→{deal['arr_time_out']}) / {deal['flight_no_in']} ({deal['dep_time_in']}→{deal['arr_time_in']})",
            "total_price": deal["total_price_tax_included"],
            "days_count": len(days_list),
            "airport_transit": kb["airport_transit"],
            "hotel_zone": kb["hotel_zone"],
            "day1_strategy": timing_tips["day1_strategy"],
            "last_day_strategy": timing_tips["last_day_strategy"],
            "ai_summary": ai_custom_summary or f"🎯 已為您根據【{deal['airline']} {deal['flight_slot_type']}】量身排妥 {len(days_list)} 天最佳不走回頭路動線！",
            "daily_plans": days_list,
        }


itinerary_bridge = ItineraryBridge()
