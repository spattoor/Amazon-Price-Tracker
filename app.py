import time
import pandas as pd
from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# CSV file for storing scraped data
CSV_FILE = "amazon_prices.csv"

# Path to product URLs file
PRODUCTS_FILE = "products.txt"

def load_product_urls():
    """Reads product URLs from products.txt"""
    try:
        with open(PRODUCTS_FILE, "r") as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"⚠️ Error: {PRODUCTS_FILE} not found.")
        return []

def get_product_details(driver, url):
    """Scrapes Amazon product title and price using Selenium."""
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page to load

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
        print(f"❌ Error fetching {url}: {e}")
        return "Error", "Error"

def scrape_amazon():
    """Scrapes Amazon for product details and logs to CSV."""
    driver = webdriver.Chrome()

    try:
        urls = load_product_urls()
        if not urls:
            print("⚠️ No URLs found. Add product links to products.txt.")
            return []

        print("\n🔄 Fetching latest prices...")
        data = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for url in urls:
            title, price = get_product_details(driver, url)
            print(f"📌 {title} - {price}")
            data.append([timestamp, title, price, url])

        # Save to CSV
        df = pd.DataFrame(data, columns=["Timestamp", "Product Name", "Price", "URL"])
        df.to_csv(CSV_FILE, mode="w", header=True, index=False)

        return data

    finally:
        driver.quit()

@app.route('/')
def home():
    """Homepage displaying the latest price data."""
    try:
        df = pd.read_csv(CSV_FILE)
        products = df.to_dict(orient="records")
    except:
        products = []

    return render_template("index.html", products=products)

@app.route('/update')
def update_prices():
    """Scrape new prices and refresh the webpage."""
    scrape_amazon()
    return "Prices updated! <a href='/'>Go back</a>"

if __name__ == "__main__":
    app.run(debug=True)
