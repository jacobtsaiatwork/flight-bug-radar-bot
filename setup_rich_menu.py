"""
LINE 官方帳號 6 格圖文選單產生與自動部署腳本 (setup_rich_menu.py)
包含 6 大核心快捷入口：
1. 🔥 Bug價與神價雷達
2. ⚡ 14天內清艙晚鳥票
3. 🔍 跨航司含行李比價 (防廉航陷阱)
4. 🌍 飛哪裡最便宜排行
5. ✨ 機票一鍵排行程展示
6. 🔔 降價雷達訂閱設定
"""

import os
from typing import Dict, Any
from PIL import Image, ImageDraw, ImageFont
from app.config import LINE_CHANNEL_ACCESS_TOKEN, BASE_DIR

WIDTH = 2500
HEIGHT = 1686
COL_W = WIDTH // 3
ROW_H = HEIGHT // 2


def generate_rich_menu_image(output_path: str = str(BASE_DIR / "rich_menu.png")) -> str:
    """使用 Pillow 繪製 2500x1686 六宮格高質感機票雷達圖文選單"""
    img = Image.new("RGB", (WIDTH, HEIGHT), color="#0F172A")
    draw = ImageDraw.Draw(img)

    cells = [
        # (col, row, bg_color, title, subtitle, badge)
        (0, 0, "#B71C1C", "Bug價神價雷達", "傳航標錯價・5折以下破盤", "【 豬隊友/布萊N風格 】"),
        (1, 0, "#E65100", "旅行社清艙票", "14天內晚鳥・含20kg托運", "【 雄獅/可樂/五福出清 】"),
        (2, 0, "#0277BD", "含行李真實比價", "廉航加行李 vs 傳航總價", "【 Skyscanner防坑試算 】"),
        (0, 1, "#00695C", "機票一鍵排行程", "依去回程起降時間排動線", "【 獨家閉環・AI智慧行程 】"),
        (1, 1, "#283593", "飛哪裡最便宜", "全網各城市底價排行榜", "【 週末快閃・連假必看 】"),
        (2, 1, "#37474F", "降價訂閱雷達", "設定目標價・破盤秒推播", "【 個人化預算守門員 】"),
    ]

    font_path = "C:/Windows/Fonts/msjhbd.ttc"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/msjh.ttc"

    try:
        title_font = ImageFont.truetype(font_path, 76)
        sub_font = ImageFont.truetype(font_path, 40)
        badge_font = ImageFont.truetype(font_path, 34)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    for col, row, bg, title, sub, badge in cells:
        x0, y0 = col * COL_W, row * ROW_H
        x1, y1 = x0 + COL_W, y0 + ROW_H
        draw.rectangle([x0, y0, x1, y1], fill=bg)
        cx, cy = x0 + COL_W // 2, y0 + ROW_H // 2
        draw.text((cx, cy - 85), title, fill="#FFFFFF", font=title_font, anchor="mm")
        draw.text((cx, cy + 15), sub, fill="#F1F5F9", font=sub_font, anchor="mm")
        draw.text((cx, cy + 95), badge, fill="#FFD54F", font=badge_font, anchor="mm")

    # 繪製白色格線
    for c in range(1, 3):
        draw.line([(c * COL_W, 0), (c * COL_W, HEIGHT)], fill="#FFFFFF", width=8)
    draw.line([(0, ROW_H), (WIDTH, ROW_H)], fill="#FFFFFF", width=8)

    img.save(output_path, quality=95)
    return output_path


def get_rich_menu_spec() -> Dict[str, Any]:
    """回傳 LINE Rich Menu 6 格設定 JSON 結構"""
    return {
        "size": {"width": WIDTH, "height": HEIGHT},
        "selected": True,
        "name": "FlightBugRadarRichMenu",
        "chatBarText": "✈️ 開啟機票清艙與Bug價雷達",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": COL_W, "height": ROW_H},
                "action": {"type": "message", "text": "Bug價雷達"},
            },
            {
                "bounds": {"x": COL_W, "y": 0, "width": COL_W, "height": ROW_H},
                "action": {"type": "message", "text": "清艙晚鳥票"},
            },
            {
                "bounds": {"x": COL_W * 2, "y": 0, "width": COL_W, "height": ROW_H},
                "action": {"type": "message", "text": "比價 東京"},
            },
            {
                "bounds": {"x": 0, "y": ROW_H, "width": COL_W, "height": ROW_H},
                "action": {
                    "type": "postback",
                    "data": "action=plan_trip&deal_id=BUG-CX-NRT-01",
                    "displayText": "✨ 用東京國泰 Bug 價航班時間排 5 天行程",
                },
            },
            {
                "bounds": {"x": COL_W, "y": ROW_H, "width": COL_W, "height": ROW_H},
                "action": {"type": "message", "text": "飛哪裡最便宜"},
            },
            {
                "bounds": {"x": COL_W * 2, "y": ROW_H, "width": COL_W, "height": ROW_H},
                "action": {"type": "message", "text": "我的訂閱"},
            },
        ],
    }


def setup_rich_menu() -> Dict[str, Any]:
    """生成圖片並（若具備 Token）呼叫 LINE Messaging API 完成綁定"""
    img_path = generate_rich_menu_image()
    spec = get_rich_menu_spec()
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return {
            "status": "mock_generated",
            "image_path": img_path,
            "rich_menu_spec": spec,
            "message": "已成功生成 6 宮格 Rich Menu 圖片與結構定義 (未設定 LINE_CHANNEL_ACCESS_TOKEN，略過遠端上傳)。",
        }

    import httpx
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=15.0) as client:
        r = client.post("https://api.line.me/v2/bot/richmenu", headers=headers, json=spec)
        if r.status_code != 200:
            return {"status": "error", "step": "create_menu", "detail": r.text}
        rich_menu_id = r.json().get("richMenuId")

        with open(img_path, "rb") as f:
            img_r = client.post(
                f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
                headers={
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "image/png",
                },
                content=f.read(),
            )
        if img_r.status_code != 200:
            return {"status": "error", "step": "upload_image", "detail": img_r.text}

        def_r = client.post(
            f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
            headers=headers,
        )
        return {
            "status": "deployed" if def_r.status_code == 200 else "partial",
            "rich_menu_id": rich_menu_id,
            "image_path": img_path,
        }


if __name__ == "__main__":
    print(setup_rich_menu())
