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
    # Render assigns a port dynamically via environment variables
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ----------------------------------------------------
# 2. MAIN AUTOMATION LOGIC
# ----------------------------------------------------
async def main_bot_executor():
    print("🚀 [Account_Alpha] Launching with saved session state...")
    
    async with async_playwright() as p:
        # Use the system's native Chrome channel to bypass installation path errors
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        # Create a persistent context or normal page depending on your session setup
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🌐 [Account_Alpha] Connecting to Discord channels...")
        
        # Keep the bot runner alive and actively listening
        try:
            while True:
                # Place your actual message listener / automation loops here
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("🛑 Bot executor execution stopped.")
        finally:
            await browser.close()

# ----------------------------------------------------
# 3. APPLICATION INITIALIZATION
# ----------------------------------------------------
if __name__ == "__main__":
    # Fire up the Flask ping web server in a separate thread so Render stays happy
    print("🌐 Starting background health-check server...")
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Run the asynchronous Playwright bot process in the main event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot_executor())
