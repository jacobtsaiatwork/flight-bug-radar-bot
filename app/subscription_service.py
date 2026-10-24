"""
🔔 個人化航線與價格門檻訂閱雷達 (Subscription Service)
支援：
- 指令訂閱：「訂閱 東京 6000」、「訂閱 大阪 8000」、「訂閱 Bug價」、「我的訂閱」、「取消訂閱 東京」
- LIFF 視覺化設定：目標航線清單、價格門檻、全網 Bug 價秒殺通知開關、清艙晚鳥票開關、艙等偏好 (經濟艙/商務艙/不限)
- 自動比對最新機票情報是否低於使用者設定的價格門檻，供排程推播端點 (`POST /api/cron/push-radar`) 發送通知
"""

import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.config import SUBSCRIBERS_FILE
from app.radar_engine import radar_engine, DESTINATION_ALIASES

CITY_NAME_BY_CODE = {
    "NRT": "東京",
    "KIX": "大阪",
    "OKA": "沖繩",
    "ICN": "首爾",
    "BKK": "曼谷",
    "EUR": "歐洲",
    "CTS": "北海道",
    "FUK": "福岡",
}


class SubscriptionService:
    def __init__(self, storage_path: Path = SUBSCRIBERS_FILE):
        self.storage_path = storage_path
        self._subscribers: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._subscribers = raw
            except Exception:
                self._subscribers = {}

    def _save(self):
        try:
            self.storage_path.write_text(
                json.dumps(self._subscribers, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def get_subscription(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self._subscribers:
            self._subscribers[user_id] = {
                "user_id": user_id,
                "routes": {
                    "NRT": {"city": "東京", "max_price": 8000},
                    "KIX": {"city": "大阪", "max_price": 9500},
                },
                "bug_fare_alert": True,
                "clearance_alert": True,
                "cabin_pref": "economy",
                "include_baggage_only": True,
            }
            self._save()
        return self._subscribers[user_id]

    def subscribe_route(self, user_id: str, dest_query: str, max_price: Optional[int] = None) -> Dict[str, Any]:
        sub = self.get_subscription(user_id)
        if "bug" in dest_query.lower() or "神價" in dest_query or "破盤" in dest_query:
            sub["bug_fare_alert"] = True
            self._save()
            return {"status": "subscribed_bug", "subscription": sub, "message": "🔥 已為您開啟【全網史詩級 Bug 價秒殺雷達】即時通知！"}

        if "清艙" in dest_query or "晚鳥" in dest_query:
            sub["clearance_alert"] = True
            self._save()
            return {"status": "subscribed_clearance", "subscription": sub, "message": "⚡ 已為您開啟【旅行社 14 天內清艙計畫票】推播通知！"}

        code = radar_engine.resolve_dest_code(dest_query) or "NRT"
        city_name = CITY_NAME_BY_CODE.get(code, dest_query)
        default_thresholds = {"NRT": 7500, "KIX": 8500, "OKA": 4500, "ICN": 6500, "BKK": 6000, "EUR": 18000}
        target_price = max_price if (max_price and max_price > 0) else default_thresholds.get(code, 8000)

        sub["routes"][code] = {
            "city": city_name,
            "max_price": int(target_price),
        }
        self._save()
        return {
            "status": "subscribed_route",
            "dest_code": code,
            "city": city_name,
            "max_price": int(target_price),
            "subscription": sub,
            "message": f"✅ 已成功設定【{city_name} ({code})】降價雷達！當含稅價低於 NT${int(target_price):,} 時將第一時間推播通知您！",
        }

    def unsubscribe_route(self, user_id: str, dest_query: str) -> Dict[str, Any]:
        sub = self.get_subscription(user_id)
        if dest_query in ["全部", "all", "清空"]:
            sub["routes"] = {}
            sub["bug_fare_alert"] = False
            sub["clearance_alert"] = False
            self._save()
            return {"status": "cleared", "subscription": sub, "message": "🧹 已清空所有航線與 Bug 價訂閱通知。"}

        code = radar_engine.resolve_dest_code(dest_query)
        if code and code in sub["routes"]:
            city_name = sub["routes"][code]["city"]
            del sub["routes"][code]
            self._save()
            return {
                "status": "unsubscribed",
                "dest_code": code,
                "city": city_name,
                "subscription": sub,
                "message": f"❌ 已取消訂閱【{city_name} ({code})】降價通知。",
            }

        return {
            "status": "not_found",
            "subscription": sub,
            "message": f"ℹ️ 您目前尚未訂閱「{dest_query}」，無需取消。",
        }

    def update_from_liff(
        self,
        user_id: str,
        routes: Dict[str, int],
        bug_fare_alert: bool = True,
        clearance_alert: bool = True,
        cabin_pref: str = "economy",
        include_baggage_only: bool = True,
    ) -> Dict[str, Any]:
        sub = self.get_subscription(user_id)
        formatted_routes = {}
        for code, price in routes.items():
            norm_code = radar_engine.resolve_dest_code(code) or code.upper()
            city_name = CITY_NAME_BY_CODE.get(norm_code, norm_code)
            formatted_routes[norm_code] = {
                "city": city_name,
                "max_price": int(price),
            }
        sub["routes"] = formatted_routes
        sub["bug_fare_alert"] = bool(bug_fare_alert)
        sub["clearance_alert"] = bool(clearance_alert)
        sub["cabin_pref"] = cabin_pref
        sub["include_baggage_only"] = bool(include_baggage_only)
        self._save()
        return sub

    def parse_and_execute_command(self, user_id: str, text: str) -> Optional[Dict[str, Any]]:
        """
        解析使用者在 LINE 輸入的訂閱指令：
        - 「訂閱 東京 6000」 / 「訂閱東京6000」 / 「訂閱 東京」
        - 「訂閱 Bug價」 / 「訂閱 清艙」
        - 「取消訂閱 東京」 / 「退訂 東京」
        """
        clean = text.strip()
        # 取消訂閱
        unsub_match = re.match(r"^(?:取消訂閱|退訂|取消追蹤)\s*(.+)$", clean)
        if unsub_match:
            target = unsub_match.group(1).strip()
            return self.unsubscribe_route(user_id, target)

        # 訂閱 [目的地] [價格門檻(選填)]
        sub_match = re.match(r"^(?:訂閱|追蹤|關注)\s*([^\d\s]+)\s*(\d+)?$", clean)
        if sub_match:
            target_city = sub_match.group(1).strip()
            price_str = sub_match.group(2)
            max_price = int(price_str) if price_str else None
            return self.subscribe_route(user_id, target_city, max_price)

        return None

    def match_deals_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """比對該訂閱者設定的航線預算門檻與 Bug 價開關，篩選出符合推播條件的特惠機票"""
        sub = self.get_subscription(user_id)
        matched_by_id: Dict[str, Dict[str, Any]] = {}

        all_deals = radar_engine.get_bug_and_promo_deals() + radar_engine.get_clearance_deals()
        for d in all_deals:
            # 1. 若開啟全網 Bug 價警報且該票為 bug_fare
            if sub.get("bug_fare_alert") and d.get("category") == "bug_fare":
                matched_by_id[d["deal_id"]] = d
                continue
            # 2. 若開啟清艙警報且該票為 clearance
            if sub.get("clearance_alert") and d.get("category") == "clearance":
                matched_by_id[d["deal_id"]] = d
                continue
            # 3. 比對特定航線與價格上限
            dest = d.get("dest")
            if dest in sub.get("routes", {}):
                threshold = sub["routes"][dest].get("max_price", 999999)
                if d["total_price_tax_included"] <= threshold:
                    matched_by_id[d["deal_id"]] = d

        results = list(matched_by_id.values())
        results.sort(key=lambda x: x["total_price_tax_included"])
        return results

    def get_all_subscribers(self) -> List[Dict[str, Any]]:
        return list(self._subscribers.values())


subscription_service = SubscriptionService()
