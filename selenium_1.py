from selenium import webdriver

# Start a Chrome browser session
driver = webdriver.Chrome()

# Open a test page
driver.get("https://www.example.com")

# Keep the browser open for a few seconds
input("Press Enter to close the browser...")

# Close the browser
driver.quit()
