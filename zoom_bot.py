import asyncio
from datetime import datetime
import os
from playwright.async_api import async_playwright

# --- 1. Load Webinar Info File (Agar zaroorat ho) ---
WEBINAR_INFO_FILE = "webinar_info.txt"


def load_webinar_details():
    if os.path.exists(WEBINAR_INFO_FILE):
        with open(WEBINAR_INFO_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# File content load karke rakhein
webinar_context = load_webinar_details()

# --- 2. Fixed Timed Messages ---
TIMED_MESSAGES = [
    {
        "time": "10:50",
        "text": "Hello Everyone !!!💖 Warm Welcome to the Bakery Business Blueprint Webinar🙏",
    },
    {
        "time": "10:52",
        "text": "Participate in the poll on your screen✅ Let us know a bit about yourself by participating in the poll on your screen✅",
    },
    {
        "time": "10:55",
        "text": "Webinar will start in 5 min⏲️ , Enjoy the VIDEO🎶",
    },
    {
        "time": "10:57",
        "text": "Please keep your Workbook/Notebook ready📝 to make lot of notes during the webinar👍",
    },
]

# --- 3. Real-Time Chat Rules (Apne Real Links Yahan Daalein) ---
KEYWORD_RULES = {
    ("price", "cost", "fee", "fees", "kitna", "pay"): (
        # REPLACE: APNA REAL PAYMENT LINK DAALEIN
        "Special Webinar Offer price is Rs. 4,999! Link: https://YOUR-ACTUAL-LINK.com/buy"
    ),
    ("workbook", "notes", "pdf", "book"): (
        # REPLACE: APNA REAL WORKBOOK LINK DAALEIN
        "You can download the Workbook from here: https://YOUR-ACTUAL-LINK.com/workbook"
    ),
    ("recording", "replay", "video"): (
        "Yes, you will get lifetime access to the recording!"
    ),
    ("certificate", "certi"): (
        "Yes, official course completion certificate will be provided."
    ),
    ("link", "buy", "join", "payment"): (
        # REPLACE: APNA REAL PAYMENT LINK DAALEIN
        "Payment Link: https://YOUR-ACTUAL-LINK.com/buy"
    ),
}

ZOOM_JOIN_URL = os.environ.get("ZOOM_JOIN_URL", "")


def get_keyword_reply(user_text):
    text_lower = user_text.lower()
    for keywords, reply in KEYWORD_RULES.items():
        if any(kw in text_lower for kw in keywords):
            return reply
    return None


async def run():
    if not ZOOM_JOIN_URL:
        print("Error: ZOOM_JOIN_URL missing!")
        return

    clean_url = ZOOM_JOIN_URL.replace("/j/", "/wc/join/")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--use-fake-ui-for-media-stream"]
        )
        page = await browser.new_page()

        print("Joining Webinar...")
        await page.goto(clean_url)

        try:
            await page.fill("#inputname", "Host Assistant")
            await page.click("#joinBtn")
            await asyncio.sleep(8)
        except Exception as e:
            print(f"Join info: {e}")

        try:
            await page.wait_for_selector(
                'button[aria-label="open the chat pane"]', timeout=30000
            )
            await page.click('button[aria-label="open the chat pane"]')
            print("Chat panel opened successfully!")
        except Exception as e:
            print(f"Chat panel error: {e}")

        sent_timed_indices = set()
        processed_chat_texts = set()

        # Monitoring Loop (~30 minutes)
        for _ in range(600):
            now_utc = datetime.utcnow()
            now_ist_mins = (now_utc.hour * 60 + now_utc.minute + 330) % (24 * 60)
            curr_time_str = f"{(now_ist_mins // 60) % 24:02d}:{now_ist_mins % 60:02d}"

            # Task 1: Fixed Timed Messages
            for idx, item in enumerate(TIMED_MESSAGES):
                if idx not in sent_timed_indices and curr_time_str >= item["time"]:
                    try:
                        chat_input = await page.wait_for_selector(
                            'div[contenteditable="true"]', timeout=5000
                        )
                        await chat_input.fill(item["text"])
                        await page.keyboard.press("Enter")
                        sent_timed_indices.add(idx)
                        print(f"[{curr_time_str}] Sent Timed: {item['text']}")
                    except Exception as err:
                        print(f"Timed send fail: {err}")

            # Task 2: Real-time Keyword Auto-Reply
            try:
                chat_nodes = await page.query_selector_all(".chat-message__text")
                for node in chat_nodes:
                    txt = await node.inner_text()
                    txt_clean = txt.strip()

                    if (
                        txt_clean
                        and txt_clean not in processed_chat_texts
                        and "Host Assistant" not in txt_clean
                    ):
                        processed_chat_texts.add(txt_clean)

                        auto_reply = get_keyword_reply(txt_clean)
                        if auto_reply:
                            chat_input = await page.wait_for_selector(
                                'div[contenteditable="true"]', timeout=5000
                            )
                            await chat_input.fill(auto_reply)
                            await page.keyboard.press("Enter")
                            print(f"Replied to '{txt_clean}' -> '{auto_reply}'")
            except Exception:
                pass

            await asyncio.sleep(3)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
