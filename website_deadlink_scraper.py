import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
from google.colab import drive
import time
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class WebsiteDeadlinkScraper:
    def __init__(self, base_url, drive_folder='WebScraperResults'):
        self.setup_logging()
        self.logger.info("Initializing WebsiteDeadlinkScraper")
        self.drive_folder = drive_folder
        self.results_file = 'deadlinks.csv'
        self.history_file = 'scan_history.csv'
        self.max_pages = 10000
        self.max_depth = 20
        self.visited_urls = set()
        self.deadlinks = []
        self.current_depth = 0
        self.base_url = self.format_and_verify_url(base_url)
        self.website_folder = urlparse(self.base_url).netloc
        self.setup()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def format_and_verify_url(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        parsed_url = urlparse(url)
        if not parsed_url.netloc.startswith('www.'):
            url = parsed_url._replace(netloc='www.' + parsed_url.netloc).geturl()

        self.logger.info(f"Attempting to connect to {url}")
        if self.check_url_accessibility(url):
            return url

        # If http fails, try https
        if url.startswith('http://'):
            https_url = 'https://' + url[7:]
            self.logger.info(f"HTTP failed. Attempting to connect to {https_url}")
            if self.check_url_accessibility(https_url):
                return https_url

        self.logger.error("Failed to connect to the website. Please check the URL and try again.")
        sys.exit(1)

    def check_url_accessibility(self, url):
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def setup(self):
        self.mount_drive()
        self.create_folder_and_files()
        self.load_history()
        self.load_existing_results()

    def mount_drive(self):
        try:
            drive.mount('/content/drive', force_remount=True)
        except Exception as e:
            self.logger.error(f"Error mounting Google Drive: {str(e)}")
            sys.exit(1)

        self.drive_path = f'/content/drive/My Drive/{self.drive_folder}/{self.website_folder}/'
        self.logger.info(f"Drive mounted successfully. Working directory: {self.drive_path}")

    def create_folder_and_files(self):
        os.makedirs(self.drive_path, exist_ok=True)
        
        results_path = os.path.join(self.drive_path, self.results_file)
        if not os.path.exists(results_path):
            pd.DataFrame(columns=['source', 'deadlink']).to_csv(results_path, index=False)
            self.logger.info(f"Created results file: {results_path}")

        history_path = os.path.join(self.drive_path, self.history_file)
        if not os.path.exists(history_path):
            pd.DataFrame(columns=['URL', 'LastScanned']).to_csv(history_path, index=False)
            self.logger.info(f"Created history file: {history_path}")

    def load_history(self):
        history_path = os.path.join(self.drive_path, self.history_file)
        self.history_df = pd.read_csv(history_path)
        self.history_df['LastScanned'] = pd.to_datetime(self.history_df['LastScanned'])

    def load_existing_results(self):
        results_path = os.path.join(self.drive_path, self.results_file)
        self.deadlinks = pd.read_csv(results_path).to_dict('records')

    def is_valid_url(self, url):
        parsed_url = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return parsed_url.netloc == base_parsed.netloc or parsed_url.netloc.endswith(base_parsed.netloc)

    def check_link(self, url):
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            return response.status_code != 200
        except requests.RequestException:
            return True

    def scrape_page(self, url, depth, force_scan=False):
        if url in self.visited_urls or depth > self.max_depth:
            return []

        self.visited_urls.add(url)
        self.current_depth = max(self.current_depth, depth)

        # Check if the page was scanned in the last 14 days
        if not force_scan and url in self.history_df['URL'].values:
            last_scanned = self.history_df.loc[self.history_df['URL'] == url, 'LastScanned'].iloc[0]
            if datetime.now() - last_scanned < timedelta(days=14):
                return []

        self.update_progress(f"Scanning: {url} (Depth: {depth})")

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            internal_links = []
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if self.is_valid_url(full_url):
                    if self.check_link(full_url):
                        self.deadlinks.append({'source': url, 'deadlink': full_url})
                        self.save_result({'source': url, 'deadlink': full_url})
                    elif full_url not in self.visited_urls:
                        internal_links.append((full_url, depth + 1))

            # Update history
            self.update_history(url)
            return internal_links

        except Exception as e:
            self.logger.error(f"Error scanning {url}: {str(e)}")
            return []

    def start_scraping(self):
        to_visit = [(self.base_url, 0)]  # (url, depth)
        with ThreadPoolExecutor(max_workers=10) as executor:
            while to_visit and len(self.visited_urls) < self.max_pages:
                futures = []
                batch = to_visit[:10]  # Take up to 10 URLs to process in parallel
                to_visit = to_visit[10:]  # Remove the processed batch from the queue
                
                for url, depth in batch:
                    force_scan = (url == self.base_url)  # Force scan for the initial URL
                    futures.append(executor.submit(self.scrape_page, url, depth, force_scan))
                
                for future in as_completed(futures):
                    new_links = future.result()
                    to_visit.extend(new_links)
                
                self.update_progress(f"Queue size: {len(to_visit)}")

        self.update_progress("Scraping completed.")
        self.logger.info(f"Scanned {len(self.visited_urls)} pages, found {len(self.deadlinks)} dead links, reached depth {self.current_depth}")

    def save_result(self, result):
        df = pd.DataFrame([result])
        results_path = os.path.join(self.drive_path, self.results_file)
        df.to_csv(results_path, mode='a', header=False, index=False)

    def update_history(self, url):
        if url in self.history_df['URL'].values:
            self.history_df.loc[self.history_df['URL'] == url, 'LastScanned'] = datetime.now()
        else:
            new_row = pd.DataFrame({'URL': [url], 'LastScanned': [datetime.now()]})
            self.history_df = pd.concat([self.history_df, new_row], ignore_index=True)

        self.save_history()

    def save_history(self):
        self.history_df.to_csv(os.path.join(self.drive_path, self.history_file), index=False)

    def update_progress(self, message):
        progress = f"\rScanned: {len(self.visited_urls)} pages, Found: {len(self.deadlinks)} deadlinks, Max Depth: {self.current_depth}, {message}"
        sys.stdout.write(progress)
        sys.stdout.flush()

def main():
    try:
        base_url = input("Enter the base URL to scrape (e.g., example.com): ")
        scraper = WebsiteDeadlinkScraper(base_url)
        scraper.start_scraping()
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        logging.error("Traceback:")
        traceback.print_exc()
        logging.error("Please check the error message and ensure Google Drive is properly mounted.")

if __name__ == "__main__":
    main()
