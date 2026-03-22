import asyncio
import argparse
import sys
import os
import random
from datetime import datetime
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import Stealth

async def human_delay(min_ms=1000, max_ms=3000):
    """Adds a random delay to simulate human behavior."""
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000.0)

async def navigate_to_orders(page):
    print("[ACTION] Navigating directly to Walmart Purchase History...")
    await page.goto("https://www.walmart.com/orders", wait_until="domcontentloaded", timeout=60000)
    
    print("[WAIT] Waiting 25 seconds for Walmart bot checks and page stability...")
    await asyncio.sleep(25)
    
    print("[CHECK] Verifying login status...")
    # Check if login is needed
    if await page.query_selector("button:has-text('Sign in'), input[type='email']"):
        print("[AUTH] Login required. Please log in manually in the browser window.")
        print("[WAIT] Waiting indefinitely for manual login and order list to appear...")
        await page.wait_for_selector("div[data-testid^='order-']", timeout=7000)
        print("[AUTH] Login successful or order list detected.")
    
    print("[STATUS] Reached Purchase History page.")

async def run(args):
    async with async_playwright() as p:
        user_data_dir = os.path.abspath(args.session_dir)
        print(f"[CONFIG] Using session directory: {user_data_dir}")
        
        print("[ACTION] Launching browser context...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            record_har_path=args.output,
            record_har_omit_content=False,
            slow_mo=100,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("[ACTION] Applying stealth measures...")
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            await navigate_to_orders(page)
            
            order_index = 0
            while True:
                # 1. Look for order index
                order_selector = f"div[data-testid='order-{order_index}']"
                # print(f"[SEARCH] Looking for order element with index {order_index}...")
                order_div = await page.query_selector(order_selector)
                
                if not order_div:
                    print(f"[FINISHED] No more order divs found on this page (stopped at index {order_index}).")
                    # Check for next page button
                    print("[CHECK] Checking for next page button...")
                    next_button = await page.query_selector("button[data-automation-id='next-pages-button']")
                    if next_button:
                        is_disabled = await next_button.get_attribute("disabled")
                        if is_disabled is None:
                            print("[ACTION] Clicking 'Next page' button...")
                            await next_button.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await asyncio.sleep(2)
                            order_index = 0
                            print("[STATUS] Navigated to next page, continuing...")
                            continue
                        else:
                            print("[FINISHED] Next page button is disabled. End of orders.")
                            break
                    else:
                        print("[FINISHED] No next page button found. End of orders.")
                        break
                                
                # 2. Click "View details" button inside this div
                view_details_btn = await order_div.query_selector("button:has-text('View details')")
                if view_details_btn:
                    # print(f"[ACTION] Clicking 'View details' for order {order_index}...")
                    await view_details_btn.click()
                    
                    # 3. Wait for the details to load (simple delay for now)
                    await human_delay(4000, 7000)
                    
                    # 4. Extract the order date from the h1 element
                    h1_element = await page.query_selector("h1")
                    order_date = None
                    if h1_element:
                        h1_text = await h1_element.text_content()
                        h1_text = h1_text.strip() if h1_text else ""
                        print(f"[INFO] Order {order_index} date: {h1_text}")
                        try:
                            date_str = h1_text.replace(" order", "").replace(" purchase", "")
                            order_date = datetime.strptime(date_str, "%b %d, %Y")
                        except ValueError:
                            print(f"[WARN] Could not parse date '{h1_text}'")
                    else:
                        print(f"[WARN] Could not find h1 element for order {order_index}")
                    
                    # 5. Check if we've reached the end date
                    if args.end and order_date:
                        end_date = datetime.strptime(args.end, "%m/%d/%Y")
                        if order_date < end_date:
                            print(f"[INFO] Reached orders before {args.end}. Stopping.")
                            break
                    
                    # 5. Navigate back to the list
                    # print(f"[ACTION] Navigating back to the orders list...")
                    await page.go_back(wait_until="domcontentloaded")
                    
                    # 5. Wait for the list to reappear before next loop
                    await page.wait_for_load_state("domcontentloaded")
                    await page.wait_for_selector("div[data-testid^='order-']", timeout=20000)
                    await human_delay(4000, 7000)
                else:
                    print(f"[ERROR] Could not find 'View details' button for order {order_index}.")
                
                # Move to next order index on this page
                order_index += 1

        except Exception as e:
            print(f"[CRITICAL] An error occurred during execution: {e}")
        finally:
            print("Closing browser...")
            await context.close()
            print(f"HAR file saved to: {args.output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simplified Walmart HAR Generator")
    parser.add_argument("--output", default="walmart_orders.har", help="Output HAR file path")
    parser.add_argument("--end", help="Stop when reaching orders before this date (MM/DD/YYYY)")
    parser.add_argument("--session-dir", default="./walmart_session", help="Directory for persistent browser session")
    
    args = parser.parse_args()
    asyncio.run(run(args))
