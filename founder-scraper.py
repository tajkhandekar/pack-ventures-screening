import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os
from dotenv import load_dotenv
from serpapi import GoogleSearch
import spacy

load_dotenv()
serp_api_key = os.getenv("SERP_API_KEY")
nlp = spacy.load("en_core_web_sm")

'''
parse_file: parses file to get company names and urls
param path: string path to a .txt file
return: list of dictionaries containing company name and url
'''
def parse_file(path: str):
    companies = []
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            if '(' in line and ')' in line:
                try:
                    name_part, url_part = line.split("(", 1)
                    name = name_part.strip()
                    url = url_part.strip("() \n")
                    companies.append({"name": name, "url": url})

                except ValueError:
                    print(f"Could not parse line: {line}")
    return companies

'''
get_founders: gets founders found for each company
param companies: list of dictionaries, where each dictionary contains the company name and company url
return: found founders for each company
'''
def get_founders(companies: []):
    output = {}
    for company in companies:
        links = get_relevant_page(company["url"])
        founders = []
        for link in links:
            for founder in founder_scraper(link):
                founders.append(founder)
            
        potential_founders = founder_scraper(company["url"])
        for potential_founder in potential_founders:
            if is_name(potential_founder):
                founders.append(potential_founder)

        if len(founders) == 0:
            search_results = get_search_results(company["name"], company["url"])
            for result in search_results:
                founders.append(result)

        output[company["name"]] = list(set(founders))
    return output

'''
get_relevant_page: finds relevant subpages on website about founders from given url
param url: company homepage url
return: list of relevant subpages
'''
def get_relevant_page(url: str):
    links = []
    RELEVANT_KEYWORDS = ['about', 'team', 'founder', 'leadership', 'company', 'who-we-are', 'our-story', 'management', 'executives']
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        text = link.get_text(strip=True).lower()
        
        base_domain = urlparse(url).netloc
        target_domain = urlparse(href).netloc

        if not target_domain or target_domain == base_domain:
            if any(keyword in href for keyword in RELEVANT_KEYWORDS) or any(keyword in text for keyword in RELEVANT_KEYWORDS):
                full_url = urljoin(url, link['href'])  
                links.append(full_url)

    links = list(set(links)) 

    return links  

'''
founder_scraper: scrape page to find founder names
param url: url of site to scrape
return: list of potential founder names
'''
def founder_scraper(url: str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    founder_sections = soup.find_all(string=lambda text: text and "founder" in text.lower())

    results = []
    for section in founder_sections:
        #check nearby elements to see if they contain a plausible founder name
        parent = section.find_parent()  
        name = None
       
        prev = parent.find_previous_sibling()
        name_candidate = ""
        if prev:
            name_candidate = prev.get_text(strip=True)
    
            if re.match(r'^[A-Z][a-z]+\s[A-Z][a-z]+', name_candidate) and is_name(name_candidate):
                name = name_candidate

        if not name:
            prev2 = parent.parent.find_previous_sibling()
            if prev2:
                name_candidate = prev2.get_text(strip=True)
                if re.match(r'^[A-Z][a-z]+\s[A-Z][a-z]+', name_candidate) and is_name(name_candidate):
                    name = name_candidate

        if name:
            results.append(extract_clean_name(name))
    
    return results

'''
is_name: filters extracted text to determine if it is likely to be a name based on length, capitalization and keywords.
param text: string containing extracted text, potentially a founder name, from a website
return: true if likely to be a name, false otherwise
'''
def is_name(text: str):
    if not text:
        return False

    text = text.strip()
    words = text.split()

    if len(words) < 2 or len(words) > 4:
        return False

    ignore_keywords = ['team', 'founder', 'join', 'ceo', 'cto', 'co-founder', 'leadership',
                       'our', 'story', 'mission', 'values', 'about', 'company']

    lowered = text.lower()
    if any(kw in lowered for kw in ignore_keywords):
        return False

    if any(not word[0].isupper() for word in words if word.isalpha()):
        return False

    return True

'''
extract_clean_name: cleans excess text from name
param text: string of text with potential founder name
return: cleaned text
'''
def extract_clean_name(text: str):
    suffix_pattern = r"(,?\s*(Ph\.?D\.?|M\.?D\.?|MBA|MSc|BSc|MS|MA|JD|DDS|DVM))+$"

    text = re.sub(r"^(Dr\.?|Prof\.?)\s+", "", text.strip())

    name = re.sub(suffix_pattern, "", text.strip(), flags=re.IGNORECASE)
    return name.strip()

'''
get_search_results: gets Google search results for founders of selected company
param name: string of company name
param url: string of company url
return: list of founder names detected
'''
def get_search_results(name: str, url: str):
    params = {
        "api_key": serp_api_key,
        "engine": "google",
        "q": f"{name} {url} founders",
        "location": "Austin, Texas, United States",
        "google_domain": "google.com",
        "gl": "us",
        "hl": "en",
        "nfpr": "1"
        }

    search = GoogleSearch(params)
    results = search.get_dict()
    founders = parse_search_results(results["organic_results"])
    return founders

'''
parse_search_results: parses search results to find founder names
param results: list of string search results
return: list of founder names
'''
def parse_search_results(results: []):
    founders = []

    for result in results:
        text = result["snippet"]
        doc = nlp(text)
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                window = doc[max(ent.start - 5, 0):ent.end + 5].text.lower()
                if "founder" in window or "co-founder" in window or "ceo" in window:
                    if is_name(ent.text):
                        founders.append(extract_clean_name(ent.text))
    return founders

if __name__ == '__main__':
    file_path = "companies.txt"
    output = get_founders(parse_file(file_path))
    with open("founders_output.json", 'w', encoding='utf-8') as f:
        json.dump(output, f)