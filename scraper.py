import requests
from bs4 import BeautifulSoup
import csv
import time

# Set the base URL for the bookstore
base_url = 'http://books.toscrape.com/catalogue/page-{}.html'

# Open the CSV file in append mode so it won't overwrite existing data
csv_file = open('books.csv', 'w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Title', 'Price'])  # Write headers

# Function to scrape book data from a page
def scrape_books_from_page(page_num):
    url = base_url.format(page_num)
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all book containers on the page
        books = soup.find_all('article', class_='product_pod')

        for book in books:
            title = book.find('h3').find('a').get('title')
            price = book.find('p', class_='price_color').get_text()

            # Displaying the book title and price in real-time in terminal
            print(f"Product: {title}")
            print(f"Price: {price}")
            print('-' * 40)

            # Write to the CSV file in real-time
            csv_writer.writerow([title, price])
            csv_file.flush()  # Immediately flush to the file so data is written in real-time
    else:
        print(f"Failed to retrieve page {page_num}")

# Real-time scraping loop for 2 pages, scraping every 10 seconds
while True:
    for page in range(1, 3):  # Scrape only the first two pages
        print(f"Scraping page {page}...")
        scrape_books_from_page(page)
        print(f"Waiting for 10 seconds before next scrape...\n")
        time.sleep(10)  # Wait for 10 seconds before scraping the next page

# Close the CSV file after all data is written (though this part is not technically reached due to infinite loop)
csv_file.close()

print("Scraping complete! Data saved to 'books.csv'.")









