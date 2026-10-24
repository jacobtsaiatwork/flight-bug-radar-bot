"""
單元與整合測試套件 (test_radar_bot.py)
測試範圍：
1. 🔥 Bug 價與破盤促銷篩選、真假特價溫度計評級 (`radar_engine.py`)
2. ⚡ 旅行社 14 天內清艙計畫票 / 晚鳥神秘票篩選 (`radar_engine.py`)
3. 🔍 Skyscanner 風格跨航司比價與「廉航加購行李 vs 傳統航空真實總價」防坑計算 (`radar_engine.py`)
4. ✨ Postback 一鍵從機票生成完整旅遊行程閉環 (`itinerary_bridge.py` & `bot_handler.py`)
5. 🔔 個人化航線與價格門檻訂閱管理 (`subscription_service.py`)
6. 🎨 機票登機證 Flex Message 結構與 Postback 按鈕驗證 (`flex_templates.py`)
7. 🌐 FastAPI Webhook、LIFF、排程推播與 API 端點驗證 (`app/main.py`)
"""

import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.radar_engine import radar_engine
from app.itinerary_bridge import itinerary_bridge
from app.subscription_service import subscription_service
from app.flex_templates import (
    build_boarding_pass_bubble,
    create_deals_carousel_flex,
    create_route_comparison_flex,
    create_flight_itinerary_flex,
)
from setup_rich_menu import get_rich_menu_spec, generate_rich_menu_image


class TestFlightBugRadarBot(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_thermometer_and_bug_fare_filtering(self):
        """測試真假特價溫度計評級與 Bug 價篩選"""
        # 史詩級 Bug 價 (< 48% 歷史均價)
        thermo_bug = radar_engine.evaluate_thermometer(6850, 15200)
        self.assertIn("史詩級 Bug 價", thermo_bug["thermometer_grade"])
        self.assertEqual(thermo_bug["saved_amount"], 15200 - 6850)
        self.assertGreaterEqual(thermo_bug["bar_percent"], 95)

        # 篩選東京 Bug 價
        nrt_deals = radar_engine.get_bug_and_promo_deals(dest_filter="東京")
        self.assertGreaterEqual(len(nrt_deals), 1)
        self.assertEqual(nrt_deals[0]["dest"], "NRT")
        self.assertTrue(nrt_deals[0]["baggage_included"])

    def test_02_clearance_deals_within_14_days(self):
        """測試旅行社 14 天內清艙計畫票與晚鳥神秘票"""
        clearance = radar_engine.get_clearance_deals(max_days_until_dep=14)
        self.assertGreaterEqual(len(clearance), 4)
        for d in clearance:
            self.assertEqual(d["category"], "clearance")
            self.assertLessEqual(d["departure_in_days"], 14)
            self.assertGreater(d["seats_left"], 0)

    def test_03_lcc_vs_fsc_true_cost_with_baggage(self):
        """測試廉航加購行李 vs 傳統航空的真實總價計算，驗證廉航隱藏費用陷阱偵測"""
        comp = radar_engine.compare_route_true_cost("東京", include_baggage=True)
        self.assertEqual(comp["dest_code"], "NRT")
        self.assertEqual(comp["city"], "東京")
        carriers = comp["carriers"]
        self.assertGreaterEqual(len(carriers), 3)

        # 排名第 1 應為國泰航空 Bug 價 (含行李真實總價 6850)
        best = comp["best_choice"]
        self.assertEqual(best["airline_code"], "CX")
        self.assertEqual(best["true_total_with_baggage"], 6850)

        # 台灣虎航表面票價 5800 < 6850，但加購 2200 行李後真實總價 8000 > 6850，必須被標記為 is_lcc_trap = True
        tiger = next(c for c in carriers if c["airline_code"] == "IT")
        self.assertEqual(tiger["base_fare_tax_included"], 5800)
        self.assertEqual(tiger["true_total_with_baggage"], 8000)
        self.assertTrue(tiger["is_lcc_trap"])

    def test_04_one_click_itinerary_from_flight_deal_closed_loop(self):
        """測試獨家閉環：點擊 Postback『✨ 用此航班時間排行程』一鍵生成貼合航班起降時間的每日行程"""
        res = self.client.post(
            "/api/simulate-postback",
            json={
                "user_id": "test_closed_loop_user",
                "data": "action=plan_trip&deal_id=BUG-CX-NRT-01",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["action"], "plan_trip")
        self.assertEqual(data["deal_id"], "BUG-CX-NRT-01")
        self.assertEqual(data["type"], "flex")

        itin = data["itinerary"]
        self.assertEqual(itin["city"], "東京")
        self.assertEqual(itin["days_count"], 5)
        self.assertIn("CX450", itin["daily_plans"][0]["morning"])
        self.assertIn("CX451", itin["daily_plans"][-1]["evening"])
        self.assertIn("Skyliner", itin["airport_transit"])

    def test_05_subscription_commands_and_matching(self):
        """測試 LINE 指令訂閱、取消訂閱與預算門檻自動比對"""
        uid = "unit_test_sub_user"
        # 訂閱 東京 7000
        r1 = self.client.post(
            "/api/simulate-chat",
            json={"user_id": uid, "message": "訂閱 東京 7000"},
        )
        self.assertEqual(r1.status_code, 200)
        sub_res = r1.json()["subscription_result"]
        self.assertEqual(sub_res["dest_code"], "NRT")
        self.assertEqual(sub_res["max_price"], 7000)

        # 比對符合該用戶的機票
        matched = subscription_service.match_deals_for_user(uid)
        self.assertGreaterEqual(len(matched), 1)

        # 取消訂閱 東京
        r2 = self.client.post(
            "/api/simulate-chat",
            json={"user_id": uid, "message": "取消訂閱 東京"},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["subscription_result"]["status"], "unsubscribed")

    def test_06_flex_boarding_pass_structure_and_buttons(self):
        """測試機票登機證 Flex 卡片 JSON 結構是否包含搶票、一鍵排行程與訂閱三大按鈕"""
        deal = radar_engine.get_deal_by_id("BUG-CX-NRT-01")
        bubble = build_boarding_pass_bubble(deal)
        self.assertEqual(bubble["type"], "bubble")
        footer_buttons = bubble["footer"]["contents"]
        self.assertEqual(len(footer_buttons), 3)

        # 檢查第 2 顆按鈕必須是 Postback『✨ 用此航班時間排行程』
        plan_btn = footer_buttons[1]["action"]
        self.assertEqual(plan_btn["type"], "postback")
        self.assertIn("✨ 用此航班時間排行程", plan_btn["label"])
        self.assertEqual(plan_btn["data"], "action=plan_trip&deal_id=BUG-CX-NRT-01")

    def test_07_fastapi_endpoints_and_cron_push(self):
        """測試 FastAPI 所有核心端點、LIFF 網頁與排程推播 API"""
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/liff").status_code, 200)
        self.assertEqual(self.client.get("/api/radar/bug-fares").status_code, 200)
        self.assertEqual(self.client.get("/api/radar/clearance").status_code, 200)
        self.assertEqual(self.client.get("/api/radar/compare?dest=大阪").status_code, 200)

        cron_res = self.client.post("/api/cron/push-radar")
        self.assertEqual(cron_res.status_code, 200)
        self.assertEqual(cron_res.json()["status"], "completed")

        # 測試 Rich Menu 生成
        spec = get_rich_menu_spec()
        self.assertEqual(len(spec["areas"]), 6)
        img_path = generate_rich_menu_image()
        self.assertTrue(img_path.endswith("rich_menu.png"))


if __name__ == "__main__":
    unittest.main()
