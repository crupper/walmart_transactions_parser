import asyncio
import argparse
import sys
import os
import random
import re
from datetime import datetime
from typing import Optional, Set
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import Stealth

async def human_delay(min_ms=1000, max_ms=3000):
    """Adds a random delay to simulate human behavior."""
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000.0)

async def wait_for_captcha(page):
    """Detects if a px-captcha is present and waits indefinitely for manual resolution."""
    captcha_selector = "#px-captcha"
    try:
        # Check if the element exists first
        if await page.query_selector(captcha_selector):
            print("[BLOCK] 'Robot or human?' challenge detected. Please solve it manually in the browser...")
            # Wait indefinitely for it to be removed from the DOM
            await page.wait_for_selector(captcha_selector, state="detached", timeout=0)
            print("[SUCCESS] Challenge cleared. Resuming...")
            await asyncio.sleep(2) 
    except Exception:
        pass

async def navigate_to_orders(page):
    print("[ACTION] Navigating directly to Walmart Purchase History...")
    await page.goto("https://www.walmart.com/orders", wait_until="domcontentloaded", timeout=60000)

    print("[WAIT] Waiting 5 seconds for page to settle...")
    await asyncio.sleep(5)

    await wait_for_captcha(page)

    print("[CHECK] Verifying login status...")

    # Check if login is needed
    if await page.query_selector("button:has-text('Sign in'), input[type='email']"):
        print("[AUTH] Login required. Please log in manually in the browser window.")
        print("[WAIT] Waiting indefinitely for manual login and order list to appear...")
        await page.wait_for_selector("div[data-testid^='order-']", timeout=120000)
        print("[AUTH] Login successful or order list detected.")
    
    print("[STATUS] Reached Purchase History page.")

async def get_order_identifier(order_div) -> Optional[str]:
    """Attempts to find the unique 21-digit order identifier from Walmart's order card."""
    # 1. Look for the 'View details' button which contains the ID in its automation attribute
    view_details_btn = await order_div.query_selector("button[data-automation-id^='view-order-details-link-']")
    if view_details_btn:
        auto_id = await view_details_btn.get_attribute("data-automation-id")
        if auto_id:
            # Extract the numeric part after 'view-order-details-link-'
            match = re.search(r'view-order-details-link-(\d+)', auto_id)
            if match:
                return match.group(1)

    # 2. Fallback: Check for links that contain the order ID
    order_link = await order_div.query_selector("a[href*='/orders/']")
    if order_link:
        href = await order_link.get_attribute("href")
        match = re.search(r'/orders/(\d+)', href)
        if match:
            return match.group(1)

    return None

async def scan_page_orders(page):
    """Scans the current page for orders and returns their metadata with date and total."""
    print("[SCAN] Scanning current page for orders...")
    all_divs = await page.query_selector_all("div[data-testid^='order-']")
    
    # Filter for strictly 'order-0', 'order-1', etc. to avoid 'order-status-tracker'
    order_divs = []
    for div in all_divs:
        testid = await div.get_attribute("data-testid")
        if testid and re.fullmatch(r'order-\d+', testid):
            order_divs.append(div)
            
    found_orders = []
    for div in order_divs:
        oid = await get_order_identifier(div)
        
        # Extract date from h2
        date_elem = await div.query_selector("h2")
        date_text = await date_elem.inner_text() if date_elem else "Unknown Date"
        
        # Extract total from the "Order total" text
        total_text = "Unknown Total"
        all_text = await div.inner_text()
        total_match = re.search(r'Order total\s+\$?([\d,.]+)', all_text)
        if total_match:
            total_text = f"${total_match.group(1)}"
            
        summary = f"{date_text} | Total: {total_text}"
        found_orders.append({
            "id": oid, 
            "summary": summary, 
            "selector_index": await div.get_attribute("data-testid")
        })
    
    print(f"[SCAN] Found {len(found_orders)} orders on this page:")
    for i, o in enumerate(found_orders):
        print(f"  {i}. [ID: {o['id']}] {o['summary']}")
    
    return found_orders

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

        # Track visited orders to avoid duplicates
        visited_orders: Set[str] = set()
        total_processed_count = 0

        try:
            await navigate_to_orders(page)
            
            while True:
                # First, ensure no captcha is blocking the list
                await wait_for_captcha(page)
                
                # 1. Scan the page to see what we have
                page_orders = await scan_page_orders(page)
                
                if not page_orders:
                    print("[FINISHED] No orders found on this page.")
                    break

                processed_on_page = 0
                for order_info in page_orders:
                    oid = order_info['id']
                    
                    # If we have an ID, check if we've visited it
                    if oid and oid in visited_orders:
                        continue
                    
                    # 2. Re-locate the order element to ensure it's fresh
                    order_selector = f"div[data-testid='{order_info['selector_index']}']"
                    order_div = await page.query_selector(order_selector)
                    
                    if not order_div:
                        print(f"[ERROR] Could not re-find order element {order_info['selector_index']}")
                        continue

                    # Double check ID if possible
                    current_oid = await get_order_identifier(order_div)
                    if oid and current_oid != oid:
                        print(f"[WARN] Order ID mismatch! Expected {oid}, found {current_oid}. Page might have shifted.")
                        break

                    # 3. Click "View details" button inside this div
                    view_details_btn = await order_div.query_selector("button:has-text('View details')")
                    if view_details_btn:
                        print(f"[ACTION] Clicking 'View details' for order: {order_info['summary']} (ID: {oid})...")
                        await view_details_btn.click()
                        
                        # 4. Wait for the details to load
                        await human_delay(4000, 7000)
                        
                        # 5. Extract the order date from the h1 element for logging/stopping
                        h1_element = await page.query_selector("h1")
                        order_date = None
                        if h1_element:
                            h1_text = await h1_element.text_content()
                            h1_text = h1_text.strip() if h1_text else ""
                            try:
                                date_str = h1_text.replace(" order", "").replace(" purchase", "")
                                order_date = datetime.strptime(date_str, "%b %d, %Y")
                            except ValueError:
                                pass
                        
                        # Mark as visited
                        if oid:
                            visited_orders.add(oid)
                        total_processed_count += 1
                        processed_on_page += 1

                        # 6. Check if we've reached the end date
                        if args.end and order_date:
                            end_date = datetime.strptime(args.end, "%m/%d/%Y")
                            if order_date < end_date:
                                print(f"[INFO] Reached orders before {args.end}. Stopping.")
                                return

                        # 7. Navigate back to the list
                        await page.go_back(wait_until="domcontentloaded")
                        
                        # 8. Wait for the list to reappear
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_selector("div[data-testid^='order-']", timeout=20000)
                        await human_delay(3000, 5000)
                    else:
                        print(f"[ERROR] Could not find 'View details' button for order.")
                
                # If we didn't process anything new on this page, try next page
                if processed_on_page == 0:
                    print("[CHECK] No new orders to process on this page. Checking for next page...")
                    next_button = await page.query_selector("button[data-automation-id='next-pages-button']")
                    if next_button:
                        is_disabled = await next_button.get_attribute("disabled")
                        if is_disabled is None:
                            print("[ACTION] Clicking 'Next page' button...")
                            await next_button.click()
                            await page.wait_for_load_state("domcontentloaded")
                            await page.wait_for_selector("div[data-testid^='order-']", timeout=20000)
                            await human_delay(4000, 7000)
                            continue
                        else:
                            print("[FINISHED] Next page button is disabled. End of orders.")
                            break
                    else:
                        print("[FINISHED] No next page button found. End of orders.")
                        break

        except Exception as e:
            print(f"[CRITICAL] An error occurred during execution: {e}")
        finally:
            print(f"Closing browser. Total orders processed: {total_processed_count}")
            await context.close()
            print(f"HAR file saved to: {args.output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simplified Walmart HAR Generator")
    parser.add_argument("--output", default="walmart_orders.har", help="Output HAR file path")
    parser.add_argument("--end", help="Stop when reaching orders before this date (MM/DD/YYYY)")
    parser.add_argument("--session-dir", default="./walmart_session", help="Directory for persistent browser session")
    
    args = parser.parse_args()
    asyncio.run(run(args))
