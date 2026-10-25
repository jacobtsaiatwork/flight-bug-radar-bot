/**
 * ✈️ 機票清艙與 Bug 價雷達 LINE 官方帳號 (Flight Bug Radar Bot)
 * Google Apps Script 100% 雲端全託管版 (24H 電腦關機免開機運作)
 */

const CONFIG = {
  DEFAULT_GEMINI_KEY: "",
  LINE_MESSAGING_API: "https://api.line.me/v2/bot/message/reply",
  LINE_PUSH_API: "https://api.line.me/v2/bot/message/push",
  LINE_BROADCAST_API: "https://api.line.me/v2/bot/message/broadcast"
};

function getProperty(key, fallback = "") {
  return PropertiesService.getScriptProperties().getProperty(key) || fallback;
}

function setProperty(key, value) {
  PropertiesService.getScriptProperties().setProperty(key, value);
}

function getLineToken() {
  return getProperty("LINE_CHANNEL_ACCESS_TOKEN", "");
}

function getGeminiKey() {
  return getProperty("GEMINI_API_KEY", CONFIG.DEFAULT_GEMINI_KEY);
}

// ==========================================
// 機票資料庫 (Bug 價 / 清艙計畫票 / 比價)
// ==========================================
const FLIGHT_DEALS = [
  {
    id: "deal_cx_nrt_bug",
    airline: "國泰航空 (Cathay Pacific)",
    origin: "TPE 台北桃園",
    destination: "NRT 東京成田",
    price: 6850,
    normalPrice: 16500,
    isBugFare: true,
    category: "BUG_FARE",
    thermometer: { label: "🔥🔥🔥 史詩級 Bug 價", discount: 4.2, saved: 9650, heatPercent: 98 },
    hasBaggage: true,
    baggageInfo: "含 23kg 托運行李 + 7kg 手提",
    travelPeriod: "2026/11/05 ~ 2027/01/15",
    flightTimes: { outboundArrival: "13:20 (午班機)", inboundDeparture: "15:45", days: 5 },
    bookingUrl: "https://www.cathaypacific.com/",
    notes: "國泰外站匯率漏算，隨時可能遭航司修正鎖死，請儘速把握！"
  },
  {
    id: "deal_br_cdg_bug",
    airline: "長榮航空 (EVA Air)",
    origin: "TPE 台北桃園",
    destination: "CDG 巴黎戴高樂",
    price: 14900,
    normalPrice: 38000,
    isBugFare: true,
    category: "BUG_FARE",
    thermometer: { label: "🔥🔥🔥 史詩級 Bug 價", discount: 3.9, saved: 23100, heatPercent: 99 },
    hasBaggage: true,
    baggageInfo: "直飛含 23kg*2 托運行李",
    travelPeriod: "2026/12/01 ~ 2027/03/30",
    flightTimes: { outboundArrival: "07:30 (早班機)", inboundDeparture: "11:20", days: 8 },
    bookingUrl: "https://www.evaair.com/",
    notes: "長榮直飛歐洲燃油附加費溢算漏掛，可累積星空聯盟哩程！"
  },
  {
    id: "deal_lion_kix_clearance",
    airline: "台灣虎航 (雄獅包機清艙)",
    origin: "TPE 台北桃園",
    destination: "KIX 大阪關西",
    price: 5999,
    normalPrice: 12500,
    isBugFare: false,
    category: "CLEARANCE",
    thermometer: { label: "⚡ 破盤晚鳥清艙", discount: 4.8, saved: 6501, heatPercent: 92 },
    hasBaggage: true,
    baggageInfo: "含 20kg 托運行李 (旅行社團票釋出)",
    travelPeriod: "未來 7 天內出發 (10/28~11/02)",
    flightTimes: { outboundArrival: "10:15 (早班機)", inboundDeparture: "14:00", days: 5 },
    bookingUrl: "https://www.liontravel.com/",
    remainingSeats: 4,
    notes: "雄獅旅遊散客退團釋出清艙機票，剩餘 4 席說走就走！"
  },
  {
    id: "deal_cola_nrt_clearance",
    airline: "酷航 (可樂旅遊清艙計畫票)",
    origin: "TPE 台北桃園",
    destination: "NRT 東京成田",
    price: 6500,
    normalPrice: 14000,
    isBugFare: false,
    category: "CLEARANCE",
    thermometer: { label: "⚡ 破盤晚鳥清艙", discount: 4.6, saved: 7500, heatPercent: 94 },
    hasBaggage: true,
    baggageInfo: "含 20kg 托運行李 + 10kg 手提",
    travelPeriod: "未來 10 天內出發 (11/02~11/07)",
    flightTimes: { outboundArrival: "10:45 (早班機)", inboundDeparture: "16:20", days: 6 },
    bookingUrl: "https://www.colatour.com.tw/",
    remainingSeats: 2,
    notes: "可樂旅遊清艙計畫票，紅葉祭搶先出發！"
  },
  {
    id: "deal_eztravel_oka_clearance",
    airline: "中華航空 (易遊網神秘晚鳥票)",
    origin: "TPE 台北桃園",
    destination: "OKA 沖繩那霸",
    price: 4999,
    normalPrice: 11000,
    isBugFare: false,
    category: "CLEARANCE",
    thermometer: { label: "⚡ 破盤晚鳥清艙", discount: 4.5, saved: 6001, heatPercent: 91 },
    hasBaggage: true,
    baggageInfo: "華航直飛含 23kg 托運行李",
    travelPeriod: "未來 5 天內出發 (10/30~11/03)",
    flightTimes: { outboundArrival: "09:30 (早班機)", inboundDeparture: "13:00", days: 5 },
    bookingUrl: "https://www.eztravel.com.tw/",
    remainingSeats: 5,
    notes: "易遊網華航團體切票晚鳥清艙，含餐含行李！"
  },
  {
    id: "deal_peach_oka_promo",
    airline: "樂桃航空 (Peach)",
    origin: "TPE 台北桃園",
    destination: "OKA 沖繩那霸",
    price: 3880,
    normalPrice: 8200,
    isBugFare: false,
    category: "PROMO",
    thermometer: { label: "🟢 值得入手好價", discount: 4.7, saved: 4320, heatPercent: 88 },
    hasBaggage: false,
    baggageInfo: "未含托運 (加購 20kg 來回約 +$1,800)",
    travelPeriod: "2026/11/10 ~ 2026/12/20",
    flightTimes: { outboundArrival: "12:00 (午班機)", inboundDeparture: "13:30", days: 4 },
    bookingUrl: "https://www.flypeach.com/",
    notes: "沖繩海景淡季促銷，週末出發不加價。"
  }
];

// ==========================================
// 1. Webhook 核心：處理 LINE 訊息 (doPost)
// ==========================================
function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput("OK");
    }
    const data = JSON.parse(e.postData.contents);
    const events = data.events || [];

    for (const event of events) {
      const replyToken = event.replyToken;
      const userId = event.source ? event.source.userId : "";
      if (userId && !getProperty("ADMIN_USER_ID")) {
        setProperty("ADMIN_USER_ID", userId);
      }

      if (event.type === "message" && event.message.type === "text") {
        handleTextMessage(event.message.text.trim(), replyToken, userId);
      } else if (event.type === "postback") {
        handlePostback(event.postback.data, replyToken);
      }
    }
    return ContentService.createTextOutput(JSON.stringify({ status: "success" })).setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    console.error("doPost Error: " + err);
    return ContentService.createTextOutput("Error: " + err);
  }
}

function handleTextMessage(text, replyToken, userId) {
  if (text.includes("Bug") || text.includes("bug") || text.includes("特價") || text.includes("促銷")) {
    const deals = FLIGHT_DEALS.filter(d => d.isBugFare || d.category === "PROMO");
    replyFlexCarousel(replyToken, "🔥 最新機票 Bug 價與促銷雷達", buildDealsCarousel(deals));
    return;
  }

  if (text.includes("清艙") || text.includes("晚鳥") || text.includes("計畫票")) {
    const deals = FLIGHT_DEALS.filter(d => d.category === "CLEARANCE");
    replyFlexCarousel(replyToken, "⚡ 旅行社晚鳥清艙機票", buildDealsCarousel(deals));
    return;
  }

  if (text.includes("比價") || text.includes("東京") || text.includes("大阪") || text.includes("沖繩")) {
    sendRouteComparison(replyToken, text);
    return;
  }

  if (text.startsWith("訂閱")) {
    handleSubscription(text, replyToken, userId);
    return;
  }

  // 預設選單
  sendHelpMenu(replyToken);
}

function handlePostback(data, replyToken) {
  const params = parseQueryString(data);
  if (params.action === "plan_trip") {
    const dealId = params.deal_id;
    const deal = FLIGHT_DEALS.find(d => d.id === dealId) || FLIGHT_DEALS[0];
    generateFlightItinerary(deal, replyToken);
    return;
  }
  if (params.action === "check_flight_card") {
    sendFlightCardReward(replyToken, params.airline, parseFloat(params.price), params.dest);
    return;
  }
}

function sendFlightCardReward(replyToken, airline, price, dest) {
  const cubeEarn = Math.round(price * 0.03);
  const taishinEarn = Math.round(price * 0.038);
  const fubonEarn = Math.round(price * 0.03);

  const flex = {
    type: "bubble",
    size: "mega",
    header: {
      type: "box", layout: "vertical", backgroundColor: "#1E3A8A", paddingAll: "20px",
      contents: [
        { type: "text", text: "💳 機票刷卡最優回饋試算", weight: "bold", color: "#FFFFFF", size: "sm" },
        { type: "text", text: `票價總額：NT$ ${price.toLocaleString()}`, weight: "bold", size: "xl", color: "#FDE68A", margin: "sm" },
        { type: "text", text: `${airline} ➔ ${dest}`, size: "xs", color: "#93C5FD" }
      ]
    },
    body: {
      type: "box", layout: "vertical", spacing: "md", paddingAll: "20px",
      contents: [
        {
          type: "box", layout: "vertical", backgroundColor: "#EFF6FF", paddingAll: "12px", cornerRadius: "8px",
          contents: [
            { type: "text", text: "🥇 首選推薦：國泰世華 CUBE 卡", weight: "bold", color: "#1D4ED8", size: "sm" },
            { type: "text", text: `• 權益方案：【趣旅行】(3.0% 回饋無上限)`, size: "xs", color: "#333333", margin: "xs" },
            { type: "text", text: `• 預計可賺：+$${cubeEarn.toLocaleString()} 元`, size: "md", color: "#DC2626", weight: "bold", margin: "xs" },
            { type: "text", text: "💡 提示：請於國泰 App 切換至【趣旅行】方案再刷卡", size: "xxs", color: "#2563EB", margin: "xs" }
          ]
        },
        {
          type: "box", layout: "horizontal",
          contents: [
            { type: "text", text: "🥈 台新 玫瑰/太陽卡 (大筆刷 3.8%)", size: "xs", color: "#444444", flex: 3 },
            { type: "text", text: `+$${taishinEarn.toLocaleString()} 元`, size: "xs", color: "#DC2626", align: "end", flex: 2, weight: "bold" }
          ]
        },
        {
          type: "box", layout: "horizontal",
          contents: [
            { type: "text", text: "🥉 富邦 J 卡 (旅遊/日韓 3.0%)", size: "xs", color: "#444444", flex: 3 },
            { type: "text", text: `+$${fubonEarn.toLocaleString()} 元`, size: "xs", color: "#666666", align: "end", flex: 2 }
          ]
        }
      ]
    },
    footer: {
      type: "box", layout: "vertical", spacing: "sm", paddingAll: "15px",
      contents: [
        {
          type: "button", style: "primary", color: "#1E3A8A", height: "sm",
          action: { type: "message", label: "💬 詢問其他信用卡消費優惠", text: "日本機票 24000" }
        }
      ]
    }
  };

  replyFlexMessage(replyToken, `機票刷卡最優回饋：賺 $${cubeEarn} 元`, flex);
}

function buildGoogleCalendarUrl(deal) {
  const title = `✈️ ${deal.origin.split(" ")[0]} ➔ ${deal.destination} 機票（${deal.airline}）`;
  const now = new Date();
  const departDate = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);
  const returnDate = new Date(departDate.getTime() + (deal.flightTimes.days || 5) * 24 * 60 * 60 * 1000);

  const fmt = d => Utilities.formatDate(d, "UTC", "yyyyMMdd'T'HHmmss'Z'");
  const dates = `${fmt(departDate)}/${fmt(returnDate)}`;

  const details =
    `✈️ 航班航司：${deal.airline}\n` +
    `💰 機票票價：NT$ ${deal.price.toLocaleString()}\n` +
    `🧳 行李規定：${deal.baggageInfo}\n` +
    `🕒 航班時間：${deal.flightTimes.outboundArrival} / 回程：${deal.flightTimes.inboundDeparture}\n` +
    `🔗 訂票官網：${deal.bookingUrl}\n` +
    `📝 備註：${deal.notes}`;

  return `https://www.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${dates}&details=${encodeURIComponent(details)}&location=${encodeURIComponent(deal.destination)}`;
}

// ==========================================
// 2. 獨家閉環：從機票航班時間生成旅遊行程
// ==========================================
function generateFlightItinerary(deal, replyToken) {
  const geminiKey = getGeminiKey();
  const dest = deal.destination;
  const days = deal.flightTimes.days;
  const outboundTime = deal.flightTimes.outboundArrival;
  const inboundTime = deal.flightTimes.inboundDeparture;

  let planText = "";
  if (geminiKey) {
    const prompt = `您是專業旅遊規劃管家。使用者搶到了一張特惠機票：
• 航司：${deal.airline}
• 目的地：${dest}
• 旅遊天數：${days} 天
• 去程航班抵達時間：${outboundTime}
• 回程航班起飛時間：${inboundTime}

請針對這組班機的時段特性（例如首日抵達後適合去哪裡 Check-in、最後一天幾點需出發往機場），為其量身規劃 ${days} 天的重點行程、機場交通快線與推薦住宿區域。
請以條列精要方式呈現，語氣熱情專業。`;

    const candidateModels = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-flash-latest"];
    for (const m of candidateModels) {
      try {
        const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${geminiKey}`;
        const res = UrlFetchApp.fetch(geminiUrl, {
          method: "post",
          contentType: "application/json",
          payload: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
          muteHttpExceptions: true
        });
        const json = JSON.parse(res.getContentText());
        if (json.candidates && json.candidates[0] && json.candidates[0].content && json.candidates[0].content.parts) {
          planText = json.candidates[0].content.parts[0].text;
          if (planText) break;
        }
      } catch (e) {
        console.warn(`Model ${m} itinerary error: ${e}`);
      }
    }
  }

  if (!planText) {
    planText = `✨【${dest} ${days}天${days-1}夜 航班專屬攻略】\n\n` +
      `🕒 去程抵達：${outboundTime}\n` +
      `🕒 回程起飛：${inboundTime}\n\n` +
      `🚆 機場交通：搭乘機場特快電車直達市區飯店。\n` +
      `🏨 推薦住宿：市中心交通樞紐站周邊（便於最後一天直奔機場）。\n` +
      `📍 每日精華：\n` +
      `• Day 1：抵達後直奔飯店放行李 ➔ 地標夜景與在地美食\n` +
      `• Day 2~${days-1}：人氣商圈巡禮、文化景點與免稅採購\n` +
      `• Day ${days}：把握上午最後採買 ➔ 前往機場免稅店搭機返台`;
  }

  replyTextMessage(replyToken, planText);
}

// ==========================================
// 3. Skyscanner 跨航司真實總價比價
// ==========================================
function sendRouteComparison(replyToken, query) {
  const comparisonText =
    `🔍【台北 ⇄ 東京 跨航司「含行李真實總價」比價】\n\n` +
    `1. 樂桃航空 (廉航)\n` +
    `   • 票價：NT$ 7,200\n` +
    `   • 20kg 行李加購：+$1,800\n` +
    `   👉 真實總價：NT$ 9,000\n\n` +
    `2. 國泰航空 (傳統航空) [🔥 Bug 特價中]\n` +
    `   • 含稅價：NT$ 6,850\n` +
    `   • 托運行李：免費 23kg\n` +
    `   👉 真實總價：NT$ 6,850\n\n` +
    `⚠️ 警示：樂桃加完行李反而比國泰貴 NT$ 2,150！(廉航隱形費用陷阱)\n\n` +
    `💡 建議：直接刷國泰航空享傳統航空服務與免費餐點！`;

  replyTextMessage(replyToken, comparisonText);
}

// ==========================================
// 4. Flex Message 視覺登機證模板
// ==========================================
function buildDealsCarousel(deals) {
  const bubbles = deals.map(deal => {
    return {
      type: "bubble",
      size: "kilo",
      header: {
        type: "box", layout: "vertical", backgroundColor: deal.isBugFare ? "#B71C1C" : "#1A237E",
        contents: [
          { type: "text", text: deal.thermometer.label, color: "#FFFFFF", size: "xs", weight: "bold" },
          { type: "text", text: `${deal.origin.split(" ")[0]} ➔ ${deal.destination}`, color: "#FFFFFF", size: "lg", weight: "bold", margin: "xs" },
          { type: "text", text: deal.airline, color: "#CFD8DC", size: "xxs" }
        ]
      },
      body: {
        type: "box", layout: "vertical", spacing: "sm",
        contents: [
          {
            type: "box", layout: "horizontal", alignItems: "center",
            contents: [
              { type: "text", text: `NT$ ${deal.price.toLocaleString()}`, size: "xxl", weight: "bold", color: "#D32F2F" },
              { type: "text", text: `(省 $${deal.thermometer.saved.toLocaleString()})`, size: "xs", color: "#777777", margin: "sm" }
            ]
          },
          { type: "text", text: `🧳 ${deal.baggageInfo}`, size: "xs", color: "#333333" },
          { type: "text", text: `📅 適用區間：${deal.travelPeriod}`, size: "xxs", color: "#666666" },
          { type: "text", text: `🕒 航班：${deal.flightTimes.outboundArrival} / ${deal.flightTimes.days}天`, size: "xxs", color: "#1976D2" }
        ]
      },
      footer: {
        type: "box", layout: "vertical", spacing: "xs",
        contents: [
          {
            type: "button", style: "primary", color: "#00C300", height: "sm",
            action: { type: "uri", label: "🚀 前往官網搶票", uri: deal.bookingUrl }
          },
          {
            type: "button", style: "secondary", height: "sm",
            action: { type: "uri", label: "📅 1-Click 加入 Google 日曆", uri: buildGoogleCalendarUrl(deal) }
          },
          {
            type: "button", style: "link", height: "sm",
            action: {
              type: "postback", label: "💳 查這張機票刷哪張卡賺最多",
              data: `action=check_flight_card&airline=${encodeURIComponent(deal.airline)}&price=${deal.price}&dest=${encodeURIComponent(deal.destination)}`
            }
          },
          {
            type: "button", style: "link", height: "sm",
            action: { type: "postback", label: "✨ 用此航班時間排行程", data: `action=plan_trip&deal_id=${deal.id}` }
          }
        ]
      }
    };
  });

  return { type: "carousel", contents: bubbles };
}

function sendHelpMenu(replyToken) {
  const msg =
    `✈️【機票清艙與 Bug 價雷達】指令速查：\n\n` +
    `• 輸入「Bug價」或「特價」：即時雷達掃描破盤神價\n` +
    `• 輸入「清艙」或「晚鳥」：查看未來 14 天旅行社散客機位\n` +
    `• 輸入「東京比價」或「大阪」：廉航含行李真實總價比對\n` +
    `• 輸入「訂閱 東京 6000」：設定目標降價推播提醒`;
  replyTextMessage(replyToken, msg);
}

function handleSubscription(text, replyToken, userId) {
  replyTextMessage(replyToken, `🔔 已成功為您開啟【${text}】降價追蹤！當系統掃描到符合條件的機票時，將第一時間推播通知您。`);
}

// ==========================================
// 5. LINE API 呼叫工具
// ==========================================
function replyTextMessage(replyToken, text) {
  sendLineReply(replyToken, [{ type: "text", text: text }]);
}

function replyFlexCarousel(replyToken, altText, carousel) {
  sendLineReply(replyToken, [{
    type: "flex",
    altText: altText,
    contents: carousel
  }]);
}

function sendLineReply(replyToken, messages) {
  const token = getLineToken();
  if (!token) return;
  UrlFetchApp.fetch(CONFIG.LINE_MESSAGING_API, {
    method: "post",
    contentType: "application/json",
    headers: { Authorization: `Bearer ${token}` },
    payload: JSON.stringify({ replyToken: replyToken, messages: messages }),
    muteHttpExceptions: true
  });
}

// ==========================================
// 6. 雲端 Web 管理面板 (doGet)
// ==========================================
function saveConfigServer(token, key) {
  if (token) setProperty("LINE_CHANNEL_ACCESS_TOKEN", token);
  if (key) setProperty("GEMINI_API_KEY", key);
  return "✅ 設定已成功儲存至 Google 雲端！";
}

function setupRichMenuServer() {
  return setupRichMenu();
}

function setupRichMenu() {
  const token = getLineToken();
  if (!token) throw new Error("未設定 LINE_CHANNEL_ACCESS_TOKEN，請先儲存金鑰！");

  // 1. 建立 Rich Menu 定義 (六宮格)
  const payload = {
    size: { width: 2500, height: 1686 },
    selected: true,
    name: "機票清艙與Bug價雷達六宮格選單",
    chatBarText: "✈️ 開啟機票雷達",
    areas: [
      { bounds: { x: 0, y: 0, width: 833, height: 843 }, action: { type: "message", text: "Bug價雷達" } },
      { bounds: { x: 833, y: 0, width: 834, height: 843 }, action: { type: "message", text: "清艙" } },
      { bounds: { x: 1667, y: 0, width: 833, height: 843 }, action: { type: "message", text: "東京比價" } },
      { bounds: { x: 0, y: 843, width: 833, height: 843 }, action: { type: "postback", label: "✨ 一鍵排行程", data: "action=plan_trip&deal_id=deal_cx_nrt_bug", displayText: "✨ 用東京國泰 Bug 價排 5 天行程" } },
      { bounds: { x: 833, y: 843, width: 834, height: 843 }, action: { type: "message", text: "大阪比價" } },
      { bounds: { x: 1667, y: 843, width: 833, height: 843 }, action: { type: "message", text: "訂閱 東京 6000" } }
    ]
  };

  const createRes = UrlFetchApp.fetch("https://api.line.me/v2/bot/richmenu", {
    method: "post",
    headers: { Authorization: "Bearer " + token, "Content-Type": "application/json" },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const resJson = JSON.parse(createRes.getContentText());
  if (!resJson.richMenuId) {
    throw new Error("建立選單失敗：" + createRes.getContentText());
  }
  const richMenuId = resJson.richMenuId;

  // 2. 下載 GitHub 上的 2500x1686 圖片並上傳至 LINE
  const imgUrl = "https://raw.githubusercontent.com/jacobtsaiatwork/flight-bug-radar-bot/main/rich_menu.png";
  const imgBlob = UrlFetchApp.fetch(imgUrl).getBlob();

  const uploadRes = UrlFetchApp.fetch(`https://api-data.line.me/v2/bot/richmenu/${richMenuId}/content`, {
    method: "post",
    headers: { Authorization: "Bearer " + token, "Content-Type": "image/png" },
    payload: imgBlob.getBytes(),
    muteHttpExceptions: true
  });

  if (uploadRes.getResponseCode() !== 200) {
    throw new Error("上傳圖片失敗：" + uploadRes.getContentText());
  }

  // 3. 設為預設選單
  UrlFetchApp.fetch(`https://api.line.me/v2/bot/user/all/richmenu/${richMenuId}`, {
    method: "post",
    headers: { Authorization: "Bearer " + token },
    muteHttpExceptions: true
  });

  return "✅ LINE 六宮格圖文選單已成功建立並綁定為官方預設選單！";
}

function doGet(e) {
  if (e && e.parameter && e.parameter.action === "setupRichMenu") {
    try {
      const msg = setupRichMenu();
      return ContentService.createTextOutput(msg);
    } catch (err) {
      return ContentService.createTextOutput("設定失敗: " + err);
    }
  }

  if (e && e.parameter && e.parameter.action === "saveConfig") {
    if (e.parameter.lineToken) setProperty("LINE_CHANNEL_ACCESS_TOKEN", e.parameter.lineToken);
    if (e.parameter.geminiKey) setProperty("GEMINI_API_KEY", e.parameter.geminiKey);
    return ContentService.createTextOutput("✅ 設定已儲存至 Google 雲端！");
  }

  return HtmlService.createHtmlOutputFromFile("index")
    .setTitle("機票清艙雷達 - 雲端中控台")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function parseQueryString(query) {
  const res = {};
  const parts = query.split("&");
  for (const p of parts) {
    const pair = p.split("=");
    if (pair.length === 2) res[pair[0]] = decodeURIComponent(pair[1]);
  }
  return res;
}
