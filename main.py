import os
import asyncio
from threading import Thread
from flask import Flask
from playwright.async_api import async_playwright

# ----------------------------------------------------
# 1. RENDER REQUIRED WEB SERVER
# ----------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot status: Running smoothly on Render!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ----------------------------------------------------
# 2. MAIN AUTOMATION LOGIC
# ----------------------------------------------------
async def main_bot_executor():
    # Grab the target channel link from Render's Environment panel
    discord_url = os.environ.get("DISCORD_URL")

    if not discord_url:
        print("❌ Error: DISCORD_URL environment variable is missing!")
        return

    print("🚀 [Account_Alpha] Launching with pre-saved storage state file...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        # Check if your auth file exists, then load it directly into the context
        if os.path.exists("auth_account_1.json"):
            print("🔑 Found auth_account_1.json! Loading saved browser session...")
            context = await browser.new_context(storage_state="auth_account_1.json")
        else:
            print("⚠️ auth_account_1.json not found! Starting a blank session.")
            context = await browser.new_context()
            
        page = await context.new_page()
        
        print(f"🌐 [Account_Alpha] Navigating to target channel...")
        await page.goto(discord_url)
        await page.wait_for_timeout(5000)
        
        print("⚡ [Account_Alpha] Actively listening for commands...")
        
        try:
            last_processed_msg = ""
            while True:
                try:
                    # Scan for message elements on the screen
                    messages = await page.query_selector_all("[class*='messageContent-']")
                    if messages:
                        latest_msg_element = messages[-1]
                        message_text = await latest_msg_element.inner_text()
                        clean_text = message_text.strip()
                        
                        if clean_text != last_processed_msg:
                            if clean_text.startswith("!start "):
                                print(f"📥 Received Command Trigger: {clean_text}")
                                last_processed_msg = clean_text
                                
                                try:
                                    parts = clean_text.split(" ")
                                    iterations = int(parts[1])
                                except Exception:
                                    iterations = 1
                                
                                chat_box = await page.wait_for_selector("[class*='textArea-'] [role='textbox']")
                                if chat_box:
                                    print(f"⏳ Running automated cycles ({iterations} iterations)...")
                                    for i in range(iterations):
                                        await chat_box.fill("!start")
                                        await chat_box.press("Enter")
                                        print(f"✅ Dispatched iteration cycle {i+1}/{iterations}")
                                        await asyncio.sleep(5)
                                        
                except Exception:
                    pass
                
                await asyncio.sleep(2)
                
        except asyncio.CancelledError:
            print("🛑 Bot executor execution stopped.")
        finally:
            await context.close()
            await browser.close()

# ----------------------------------------------------
# 3. APPLICATION INITIALIZATION
# ----------------------------------------------------
if __name__ == "__main__":
    print("🌐 Starting background health-check server...")
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot_executor())
