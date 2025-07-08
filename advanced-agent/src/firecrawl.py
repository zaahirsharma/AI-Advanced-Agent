import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv

load_dotenv()

class FirecrawlService:
    # Constructor to initialize class, as soon as class instance is created run set-up steps
    def __init__(self):
        
        # Get the API key from environment variables
        api_key = os.getenv("FIRECRAWL_API_KEY")
        # If the API key is not loaded properly, raise an error
        if not api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable is not set.")
        
        # Initialize the Firecrawl application with the API key
        self.app = FirecrawlApp(api_key=api_key)
        
    # Search for companies using the Firecrawl app
    def search_companies(self, query: str, num_results: int = 5):
        # Need query and only want 5 results
        try:
            result = self.app.search(
                query=f"{query} company pricing", # Searches company name/query and pricing
                limit=num_results, # Limit the number of results
                scrape_options=ScrapeOptions(
                    formats=["markdown"] # Format the results in markdown for better readability
                )
            )
            return result
        except Exception as e:
            print(f"Error during search: {e}")
            return []
        
    # Scrape company pages using the Firecrawl app
    def scrape_company_pages(self, url: str):
        # Given a url for a site to scrape
        try:
            result = self.app.scrape_url(
                url, # URL to scrape
                formats=["markdown"], # Format the results in markdown
            )
            return result
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None