import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


# Instagram credentials
username = "nykamyha@forexnews.bg"
password = "Happydesk@02"


# --- Read the CSV file with encoding fix ---
input_file = "inputfile.csv"  
output_file = "output.csv"

df = pd.read_csv("inputfile.csv", encoding="utf-8-sig")
if 'profile_url' not in df.columns:
    print("Columns in CSV:", df.columns.tolist())
    raise ValueError("CSV must have a column named 'profile_url' containing Instagram profile links")

# --- Set up Selenium ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-popup-blocking")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.instagram.com/accounts/login/")

time.sleep(10)  # Wait for page to load

# Accept cookies popup if it appears
try:
    cookies_btn = driver.find_element(By.XPATH, '//button[text()="Allow all cookies"]')
    cookies_btn.click()
    time.sleep(2)
except:
    pass

# Enter username
username_input = driver.find_element(By.NAME, "username")
username_input.send_keys(username)

# Enter password
password_input = driver.find_element(By.NAME, "password")
password_input.send_keys(password)

# Submit form
password_input.send_keys(Keys.RETURN)

time.sleep(5)


def safe_find(xpath):
    try:
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""

def click_more_if_exists():
    try:
        more_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//button[normalize-space(text())="more"]'))
        )
        more_button.click()
        time.sleep(1)
    except TimeoutException:
        pass

def parse_followers(followers_text):
    if not followers_text:
        return 0
    followers_text = followers_text.lower().replace(',', '').strip()
    multiplier = 1
    if 'k' in followers_text:
        multiplier = 1_000
        followers_text = followers_text.replace('k', '')
    elif 'm' in followers_text:
        multiplier = 1_000_000
        followers_text = followers_text.replace('m', '')
    try:
        return int(float(followers_text) * multiplier)
    except:
        return 0

# --- Function to scrape profile ---
def scrape_profile(url):
    driver.get(url)

    # Wait for profile header to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "header"))
        )
    except TimeoutException:
        print(f"⚠ Timeout waiting for profile: {url}")
        return None

    full_name = safe_find('//header//section//h2') or safe_find('//header//h1')
    category = safe_find('//header//div[contains(@class,"_ap3a")]')
    bio_visible = safe_find('//header//span[contains(@class,"_ap3a")]')


    # Try to click "more" to get full bio if exists
    click_more_if_exists()
    bio_full = safe_find('//header//span[contains(@class,"_ap3a _aaco _aacu _aacx _aad7 _aade")]')
    

    # Followers count
    try:
        followers_raw = driver.find_element(By.XPATH, '//ul/li[2]//span').get_attribute('title') or driver.find_element(By.XPATH, '//ul/li[2]//span').text
    except:
        followers_raw = ""
   # followers = parse_followers(followers_raw)

    posts = safe_find('//ul/li[1]//span')
    

    return {
        "url": url,
        "full_name": full_name,
        "category": category,
        "bio_visible": bio_visible,
        "bio_full": bio_full,
        "followers_raw": followers_raw,
        "posts": posts
    }

# --- Loop through all URLs ---
results = []
for profile_url in df['profile_url']:
    print(f"Scraping: {profile_url}")
    try:
        data = scrape_profile(profile_url)
        if data:
            results.append(data)
        # Add delay to avoid rate limiting
        time.sleep(3)
    except Exception as e:
        print(f"Error scraping {profile_url}: {e}")

# --- Save to CSV ---
output_df = pd.DataFrame(results)
output_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"Scraping completed. Data saved to {output_file}")

driver.quit()
