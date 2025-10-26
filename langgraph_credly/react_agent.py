import os
import json
from typing import Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

# -------------------- Tool Definition --------------------

@tool
def parse_credly_badge(url):
    """
    Parse Credly badge details from the given URL in headless mode.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=options)
    badge_details = {}

    try:
        print(f"\n🔗 Loading badge page: {url}")
        driver.get(url)

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.cr-badges-full-badge__head-group"))
        )

        # --- Extract badge name ---
        try:
            badge_name = driver.find_element(By.CSS_SELECTOR, "div.cr-badges-full-badge__head-group").text
            badge_details['badge_name'] = badge_name
        except NoSuchElementException:
            badge_details['badge_name'] = "N/A"

        # --- Extract certificate holder ---
        try:
            cert_holder = driver.find_element(By.CSS_SELECTOR, "p.badge-banner-issued-to-text__name-and-celebrator-list").text
            badge_details['certificate_holder'] = cert_holder
        except NoSuchElementException:
            badge_details['certificate_holder'] = "N/A"

        # --- Extract issue and expiration dates ---
        try:
            detail_items = driver.find_elements(By.CSS_SELECTOR, "span.cr-badge-banner-expires-at-text")
            if detail_items:
                p_element = detail_items[0].find_element(By.XPATH, "./ancestor::p")
                full_text = p_element.text.replace("\n", " ")
                badge_details['dates'] = full_text
            else:
                badge_details['dates'] = "N/A"
        except NoSuchElementException:
            badge_details['dates'] = "N/A"

        return badge_details

    except TimeoutException:
        print("⏳ Timeout: Page took too long to load.")
        return None
    except Exception as e:
        print(f"⚠️ Error: {str(e)}")
        return None
    finally:
        driver.quit()


@tool
def credly_points(badge_json: Any):
    """
    Assigns credit points to a Credly badge based on its name.
    Accepts either a dict (badge info) or a file path (str) to a JSON file.
    """
    # Load JSON if a file path is passed
    if isinstance(badge_json, str):
        with open(badge_json, "r") as f:
            badge_data = json.load(f)
    else:
        badge_data = badge_json  # already a dict

    badge_name = badge_data.get("badge_name", "").lower()

    # --- Simple scoring logic ---
    if "foundation" in badge_name:
        points = 1
    elif "associate" in badge_name:
        points = 2
    elif "professional" in badge_name or "expert" in badge_name:
        points = 3
    else:
        points = 1  # default

    badge_data["credit_points"] = points

    # Save updated file
    with open("badge_details_with_points.json", "w") as f:
        json.dump(badge_data, f, indent=2)

    return badge_data

# -------------------- Tools List --------------------

tools = [parse_credly_badge, credly_points]

# -------------------- LLM Setup --------------------

groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")

llm = ChatGroq(
    groq_api_key=groq_api_key,
    model="openai/gpt-oss-20b"
)

graph = create_react_agent(llm, tools)

# -------------------- MAIN SCRIPT --------------------

if __name__ == "__main__":
    # Ask user for Credly badge URL
    url = input("Enter your Credly badge URL: ").strip()

    if not url:
        print("❌ No URL provided. Exiting.")
        exit()

    badge_info = parse_credly_badge(url)

    if badge_info:
        print("\n✅ === Badge Details ===")
        print(json.dumps(badge_info, indent=2))

        # Save raw badge data
        with open("badge_details.json", "w") as f:
            json.dump(badge_info, f, indent=2)

        updated = credly_points("badge_details.json")

        print("\n🏅 === Badge with Credit Points ===")
        print(json.dumps(updated, indent=2))

        print("\n💾 Details saved to:")
        print(" - badge_details.json")
        print(" - badge_details_with_points.json")

    else:
        print("❌ Failed to parse badge details.")
