from selenium import webdriver

# Start Chrome browser
driver = webdriver.Chrome()  # Make sure chromedriver is installed and in PATH
driver.get('https://your-website.com/login')

# (Optional) Automate login here if needed
# driver.find_element(...).send_keys(...)
# driver.find_element(...).click()

# Extract cookies after login
cookies = driver.get_cookies()
cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

# Example: Get a specific cookie value
sessionid = cookie_dict.get('sessionid')  # Replace with your cookie name

# Use in requests
import requests
headers = {'Cookie': f'sessionid={sessionid}'}
response = requests.get('https://your-website.com/api', headers=headers)

driver.quit()