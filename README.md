# Getting Started

1. Create a .env file in the founder_scraper folder to store the SerpApi key as follows: SERP_API_KEY = "key info (in email)"
2. Create a new virtual environment after cloning repository
3. Install dependencies with: pip install -r requirements.txt
4. Run founder-scraper.py: python founder-scraper.py
5. View output in the founders_output.json file

# My Approach
I used web scraping to automatically find founder names by scraping the company websites given and implementing SerpApi (Google Search API). 

For each company in the given text file, I first scraped the given company website for links to find relevant website subpages that founder names could potentially be on.

Then, I scraped every relevant subpage to find sections that have the word "founder". After, I checked every nearby element to see if they included a potential founder name. For each potential founder name, I determined if it is likely to be a name based on length, capitalization and keywords. If it was determined to be a founder name, I cleaned the name using regular expressions and added it to the list of founders for the company. 

If no relevant subpages were found, I scraped the homepage instead using the same method.

If no founders were found on the company website, I used SerpApi to get the organic results from searching the founders of the website in Google. I assumed that searching up the company name and URL would yield results relevant to the company given. I used natural language processing using SpaCY to find potential founder names from the results and then determined if it was a founder name and cleaned the text if it was.

After adding all founder names to a list for each company, I removed duplicates and added it to the dictionary to output in a JSON file.

# Future Improvements
* Some of the founder names I collected include founders from other companies with the same name. To reduce this, I would use natural language processing and keyword frequency when scraping the company website to find keywords relating to the company, and include them in the Google search so that the results are more likely to be tailored to the company and not other companies with the same name
* Scraping Twitter to find potential founders for a company as it is used by many people in the tech industry to share ideas and thoughts
* Using a combination of scraping each website and SerpApi instead of separately to be able to cross-check accuracy of founder information across both data sources 
