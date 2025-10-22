# Data from en.wiktionary.org, licensed under CC BY-SA 3.0.
import requests
import time
import json
from urllib.parse import quote
import mwparserfromhell
import logging
import os
import tempfile

# Set up logging
def setup_logging(language):
    log_file = f"wiktionary_{language.lower()}_errors.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return log_file

# API base URL for en.wiktionary.org
API_BASE = "https://en.wiktionary.org/w/api.php"

# Headers to mimic a polite browser request
HEADERS = {
    "User-Agent": "EgyptianLemmasScraper/1.0 (email here)",  # Replace with your info!
    "Accept": "application/json",
    "Referer": "https://en.wiktionary.org/wiki/Category:{}_lemmas"
}

def get_category_members(category, limit=500):
    """Fetch all pages in a category, paginated."""
    members = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": limit,
            "format": "json"
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        try:
            response = requests.get(API_BASE, params=params, headers=HEADERS, timeout=10)
            handle_response(response, "categorymembers")
            data = response.json()
            if "error" in data:
                logging.error(f"API Error in categorymembers: {data['error']}")
                raise ValueError(f"API Error: {data['error']}")
            members.extend([m['title'] for m in data["query"]["categorymembers"]])
            if "continue" not in data:
                break
            cmcontinue = data["continue"]["cmcontinue"]
            time.sleep(1)  # Rate limit
        except (requests.RequestException, ValueError) as e:
            logging.error(f"Error fetching category members: {e}")
            time.sleep(5)  # Wait longer before retrying
            continue
    return members

def handle_response(response, context=""):
    """Handle and log response errors."""
    if response.status_code >= 400:
        logging.error(f"{context} - Status {response.status_code}: {response.text[:1000]}")
        response.raise_for_status()

def get_page_wikitext(title, retries=3):
    """Fetch full wikitext for a page with retries."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2",
        "format": "json"
    }
    for attempt in range(retries):
        try:
            response = requests.get(API_BASE, params=params, headers=HEADERS, timeout=10)
            handle_response(response, f"Page fetch for {title}")
            data = response.json()
            if "error" in data:
                logging.error(f"API Error for {title}: {data['error']}")
                return None
            pages = data["query"]["pages"]
            if not pages:
                logging.warning(f"No pages returned for {title}")
                return None
            page = pages[0]
            if page.get("missing"):
                logging.warning(f"Page missing: {title}")
                return None
            if "revisions" not in page or not page["revisions"]:
                logging.warning(f"No revisions for {title}")
                return None
            rev = page["revisions"][0]
            if "slots" not in rev or "main" not in rev["slots"]:
                logging.error(f"No main slot for {title}: {json.dumps(page, ensure_ascii=False)}")
                return None
            slot = rev["slots"]["main"]
            if "content" not in slot:
                logging.error(f"No content for {title}: {json.dumps(page, ensure_ascii=False)}")
                return None
            return slot["content"]
        except (requests.RequestException, ValueError) as e:
            logging.error(f"Attempt {attempt + 1} failed for {title}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to fetch {title} after {retries} attempts")
                return None
    return None

def extract_language_section(wikitext, title, language):
    """Parse wikitext and extract the language-specific section."""
    if not wikitext:
        return ""
    try:
        parsed = mwparserfromhell.parse(wikitext)
        for section in parsed.get_sections([language]):
            return str(section)
        logging.warning(f"No '{language}' section found for {title}")
        return wikitext
    except Exception as e:
        logging.error(f"Error parsing wikitext for {title}: {e}")
        return wikitext

def save_lemma(data, output_file, title):
    """Save a single lemma to the JSON file."""
    existing_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            logging.error(f"Error reading {output_file}: {e}")
    
    existing_data[title] = data
    
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".json") as temp_file:
        json.dump(existing_data, temp_file, ensure_ascii=False, indent=2)
    
    try:
        os.replace(temp_file.name, output_file)
        logging.info(f"Saved lemma {title} to {output_file}")
    except Exception as e:
        logging.error(f"Error replacing {output_file}: {e}")
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)

def load_lemmas_list(lemma_file):
    """Load lemma list from file if it exists."""
    if os.path.exists(lemma_file):
        with open(lemma_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_lemmas_list(lemmas, lemma_file):
    """Save lemma list to file."""
    with open(lemma_file, "w", encoding="utf-8") as f:
        json.dump(lemmas, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved lemma list to {lemma_file}")

def main():
    # Prompt for language selection
    valid_languages = ["Coptic", "Egyptian", "Demotic"]
    print("Available languages: Coptic, Egyptian, Demotic")
    language = input("Enter language to scrape: ").strip().capitalize()
    if language not in valid_languages:
        print(f"Invalid language. Choose from: {', '.join(valid_languages)}")
        logging.error(f"Invalid language selected: {language}")
        return
    
    # Set up language-specific variables
    category = f"{language} lemmas"
    output_file = f"{language.lower()}_lemmas.json"
    lemma_file = f"{language.lower()}_lemmas_list.json"
    log_file = setup_logging(language)
    HEADERS["Referer"] = HEADERS["Referer"].format(language)  # Update Referer for language
    
    logging.info(f"Starting {language} lemma collection...")
    print(f"Checking for existing {language} lemma list...")
    lemmas = load_lemmas_list(lemma_file)
    
    if lemmas is None:
        print(f"Fetching list of {language} lemmas...")
        logging.info(f"Fetching list of {language} lemmas...")
        lemmas = get_category_members(category)
        save_lemmas_list(lemmas, lemma_file)
    else:
        print(f"Loaded {len(lemmas)} lemmas from {lemma_file}")
        logging.info(f"Loaded {len(lemmas)} lemmas from {lemma_file}")
    
    print(f"Found {len(lemmas)} lemmas.")
    logging.info(f"Found {len(lemmas)} lemmas.")
    
    # Load existing lemmas to skip processed ones
    processed_titles = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                processed_titles = set(json.load(f).keys())
            print(f"Skipping {len(processed_titles)} already processed {language} lemmas.")
            logging.info(f"Skipping {len(processed_titles)} already processed {language} lemmas.")
        except Exception as e:
            logging.error(f"Error reading {output_file} for processed titles: {e}")
    
    total_processed = 0
    for i, title in enumerate(lemmas, 1):
        if title in processed_titles:
            print(f"Skipping {i}/{len(lemmas)}: {title} (already processed)")
            logging.info(f"Skipping {i}/{len(lemmas)}: {title} (already processed)")
            continue
        
        print(f"Processing {i}/{len(lemmas)}: {title}")
        logging.info(f"Processing {i}/{len(lemmas)}: {title}")
        wikitext = get_page_wikitext(title)
        if wikitext:
            language_section = extract_language_section(wikitext, title, language)
            lemma_data = {
                "full_wikitext": wikitext,
                f"{language.lower()}_section": language_section
            }
            save_lemma(lemma_data, output_file, title)
            total_processed += 1
        else:
            logging.warning(f"Skipped {title} due to fetch failure")
        time.sleep(1.5)  # Rate limit delay
    
    print(f"Done! Processed {total_processed} new {language} lemmas. Data saved to {output_file}")
    logging.info(f"Done! Processed {total_processed} new {language} lemmas. Data saved to {output_file}")

if __name__ == "__main__":
    main()