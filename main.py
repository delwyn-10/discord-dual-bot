import os
import asyncio
import re
from flask import Flask
from threading import Thread
from playwright.async_api import async_playwright

# 1. Setup background web server for Render pings
app = Flask('')

@app.route('/')
def home():
    return "Dual Cooldown Bot Status: Live"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Automated Loop Core Logic
async def run_single_account(state_json_file, account_name, cooldown_seconds, start_delay):
    async with async_playwright() as p:
        print(f"🚀 [{account_name}] Launching with saved session state...")
        
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        # Force Playwright to look in the custom Render cache directory
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/render/.cache/ms-playwright"
        
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        if os.path.exists(state_json_file):
            context = await browser.new_context(storage_state=state_json_file)
        else:
            print(f"❌ Error: {state_json_file} not found. Cannot bypass login!")
            await browser.close()
            return
            
        page = await context.new_page()
        print(f"🌐 [{account_name}] Connecting to Discord channels...")
        await page.goto("https://discord.com/channels/@me")
        
        last_processed_id = None

        while True:
            try:
                chat_box = page.locator('div[role="textbox"]').first
                
                if await chat_box.is_visible():
                    chat_elements = await page.query_selector_all('li[class*="messageListItem"]')
                    
                    if chat_elements:
                        last_element = chat_elements[-1]
                        element_id = await last_element.get_attribute("id")
                        
                        if element_id and element_id != last_processed_id:
                            text_content = await last_element.inner_text()
                            
                            match = re.search(r'!start\s+(\d+)', text_content.lower())
                            
                            if match:
                                loop_count = int(match.group(1))
                                last_processed_id = element_id
                                total_packs = 75 * loop_count
                                
                                # Apply individual start stagger delay to prevent simultaneous input clashes
                                if start_delay > 0:
                                    await asyncio.sleep(start_delay)
                                
                                # 1. Send START notice
                                await chat_box.focus()
                                await chat_box.click()
                                await chat_box.fill(f"[{account_name}] Opening 75 x {loop_count} packs ({cooldown_seconds}s CD)... 🚀")
                                await chat_box.press("Enter")
                                await asyncio.sleep(4) 
                                
                                # 2. Run execution loop
                                for i in range(loop_count):
                                    print(f"[{account_name}] Command {i+1}/{loop_count}...")
                                    await chat_box.focus()
                                    await chat_box.click()
                                    
                                    await chat_box.press("Control+A")
                                    await chat_box.press("Delete")
                                    
                                    await chat_box.type("/packs", delay=100)
                                    await asyncio.sleep(0.5)
                                    await chat_box.press("Enter")
                                    await asyncio.sleep(0.5)
                                    
                                    await chat_box.type("75", delay=100)
                                    await asyncio.sleep(0.5)
                                    await chat_box.press("Enter")
                                    
                                    # Custom Cooldown pacing applied per account
                                    await asyncio.sleep(cooldown_seconds)
                                
                                # 3. Send STOP summary
                                await chat_box.focus()
                                await chat_box.click()
                                await chat_box.fill(f"[{account_name}] Session complete. Total packs opened: {total_packs} ✨")
                                await chat_box.press("Enter")
                                
            except Exception as e:
                print(f"❌ [{account_name} Error]: {e}")
                
            await asyncio.sleep(2)

# 3. Orchestrate both configurations concurrently
async def main_bot_executor():
    await asyncio.gather(
        # Account 1: Uses a 16s cooldown, starts immediately (0s delay)
        run_single_account("auth_account_1.json", "Account_Alpha", cooldown_seconds=16, start_delay=0),
        
        # Account 2: Uses a 28s cooldown, waits 4s to stay desynced from Account 1
        run_single_account("auth_account_2.json", "Account_Beta", cooldown_seconds=28, start_delay=4)
    )

if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_bot_executor())
