import asyncio
import csv
from playwright.async_api import async_playwright, TimeoutError
import os

async def get_order_details():
    """
    Scrapes order details from Walmart.com and saves them to a CSV file.

    This script opens a browser, prompts the user to log in, then navigates
    to the orders page, clicks into each order, and extracts the item details.
    """

    # List to hold all the extracted item data
    all_items_data = []

    # CSV file name
    csv_filename = "walmart_order_items.csv"

    print("Launching browser...")
    async with async_playwright() as p:
        # Launch browser in a non-headless mode so you can interact with it for login
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # Navigate to the Walmart orders page
            await page.goto("https://www.walmart.com/orders", wait_until="domcontentloaded")

            # Wait for the user to log in. The script will continue once it detects
            # a key element from the orders page, indicating a successful login.
            print("Please log in to your Walmart account in the browser window that just opened.")
            print("The script will automatically continue once it detects the order history page.")

            # Wait for the main content of the orders page to be visible
            await page.wait_for_selector('div[data-testid="orders-list-header"]', timeout=300000)
            print("Login successful. Scraping orders...")

            while True:
                # Find all order links on the current page
                order_link_selectors = await page.query_selector_all('a[data-testid="order-card-link"]')

                # Process each order on the page
                for i in range(len(order_link_selectors)):
                    try:
                        # Re-select the link in case of page navigation or reload
                        order_link_element = (await page.query_selector_all('a[data-testid="order-card-link"]'))[i]
                        
                        # Get the order number from the title for debugging
                        order_number = await order_link_element.get_attribute("aria-label")
                        print(f"Opening order: {order_number}")

                        # Click the link to view order details
                        await order_link_element.click()

                        # Wait for the order details page to load
                        await page.wait_for_selector('div[data-testid="order-details-item-list"]')

                        # Find all item detail sections
                        item_sections = await page.query_selector_all('div[data-testid="order-details-item-card"]')

                        if not item_sections:
                            print(f"No items found for order {order_number}. Skipping.")
                            # Go back to the orders list page
                            await page.go_back()
                            continue

                        # Extract item details
                        for item_section in item_sections:
                            try:
                                item_name_elem = await item_section.query_selector('a[data-testid="order-details-item-name"]')
                                item_name = await item_name_elem.inner_text() if item_name_elem else 'N/A'

                                item_price_elem = await item_section.query_selector('div[data-testid="order-details-item-price"]')
                                item_price = await item_price_elem.inner_text() if item_price_elem else 'N/A'

                                item_quantity_elem = await item_section.query_selector('div[data-testid="order-details-item-quantity"]')
                                item_quantity = await item_quantity_elem.inner_text() if item_quantity_elem else 'N/A'
                                
                                # Clean up the data
                                item_name = item_name.strip()
                                item_price = item_price.replace('Price', '').strip()
                                item_quantity = item_quantity.replace('Qty', '').strip()

                                all_items_data.append({
                                    "order_number": order_number,
                                    "item_name": item_name,
                                    "quantity": item_quantity,
                                    "price": item_price
                                })

                                print(f"  - Scraped item: {item_name} (Qty: {item_quantity})")

                            except Exception as e:
                                print(f"Error scraping item details for order {order_number}: {e}")

                        # Go back to the orders list page
                        await page.go_back()
                        # Wait for the list to reload
                        await page.wait_for_selector('div[data-testid="orders-list-header"]')

                    except Exception as e:
                        print(f"Failed to process an order link: {e}")
                        # If we fail to process an order, we should go back to the list
                        # This handles cases where we might have navigated away
                        await page.go_back()

                # Check for "Next" button to paginate
                next_button = await page.query_selector('button[data-testid="next-button"][aria-disabled="false"]')
                if next_button:
                    print("Navigating to the next page of orders...")
                    await next_button.click()
                    # Wait for the new page of orders to load
                    await page.wait_for_selector('a[data-testid="order-card-link"]')
                else:
                    print("No more pages to scrape.")
                    break

        except TimeoutError:
            print("Timeout while waiting for the orders page. Please ensure you are logged in correctly.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print("Closing browser...")
            await browser.close()
            
    # Write the data to a CSV file
    if all_items_data:
        try:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ["order_number", "item_name", "quantity", "price"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(all_items_data)

            print(f"Successfully saved all order items to '{csv_filename}'.")
            
        except Exception as e:
            print(f"An error occurred while writing the CSV file: {e}")
    else:
        print("No item data was collected. The CSV file was not created.")

# Run the main function
if __name__ == "__main__":
    asyncio.run(get_order_details())

