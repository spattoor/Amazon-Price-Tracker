import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

# CSV file for storing scraped data
CSV_FILE = "amazon_prices.csv"

# Path to the products file
PRODUCTS_FILE = "products.txt"

def load_product_urls():
    """Reads product URLs from products.txt"""
    try:
        with open(PRODUCTS_FILE, "r") as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f" Error: {PRODUCTS_FILE} not found.")
        return []

def get_product_details(driver, url):
    """Scrapes Amazon product title and price using Selenium."""
    try:
        driver.get(url)
        time.sleep(2)  # Wait for the page to load

        # Extract product title
        try:
            title = driver.find_element(By.ID, "productTitle").text.strip()
        except:
            title = "Title Not Found"

        # Extract product price
        try:
            price = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.strip()
        except:
            price = "Price Not Available"

        return title, price

    except Exception as e:
        print(f" Error fetching {url}: {e}")
        return "Error", "Error"

def log_to_csv(data):
    """Logs product details to a CSV file."""
    df = pd.DataFrame(data, columns=["Timestamp", "Product Name", "Price", "URL"])
    df.to_csv(CSV_FILE, mode="a", header=not pd.io.common.file_exists(CSV_FILE), index=False)
    print(" Data saved to CSV.")

def main():
    """Main loop for real-time tracking every 10 seconds."""
    driver = webdriver.Chrome()  # Use Chrome browser

    try:
        while True:
            urls = load_product_urls()
            if not urls:
                print(" No URLs found. Add product links to products.txt.")
                break

            print("\n Fetching latest prices...")
            data = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for url in urls:
                title, price = get_product_details(driver, url)
                print(f" {title} - {price}")
                data.append([timestamp, title, price, url])

            log_to_csv(data)
            print(" Waiting 10 seconds before next update...\n")
            time.sleep(10)  # Wait 10 seconds before next run

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
