# Website Deadlink Scraper

## Overview

This Python script is designed to scan websites for dead links (broken URLs) and save the results. It's particularly useful for website maintainers, SEO specialists, and developers who want to ensure their websites are free of broken links.

## Features

- **Multithreaded Scanning**: Utilizes Python's `ThreadPoolExecutor` for efficient, parallel processing of web pages.
- **Google Drive Integration**: Automatically saves results and scan history to Google Drive, making it easy to run in Google Colab.
- **Depth Control**: Configurable maximum depth for scanning, preventing endless crawling of large websites.
- **Scan History**: Keeps track of previously scanned pages to avoid unnecessary rescanning within a specified time frame.
- **Subdomain Handling**: Correctly processes and includes subdomains of the main website.
- **Detailed Logging**: Provides comprehensive logs for debugging and monitoring the scanning process.
- **Progress Updates**: Real-time console updates on scanning progress.

## Requirements

- Python 3.6+
- Required libraries: 
  - requests
  - beautifulsoup4
  - pandas
  - google-colab (for Google Drive integration)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/DrKenReid/website-deadlink-scraper.git
   ```
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Open the script in Google Colab or your preferred Python environment.
2. Run the script:
   ```python
   python website_deadlink_scraper.py
   ```
3. When prompted, enter the base URL of the website you want to scan (e.g., 'example.com').
4. The script will start scanning and display progress in real-time.
5. Results will be saved in your Google Drive under the folder 'WebScraperResults/[website_name]'.

## Configuration

You can modify the following parameters in the `WebsiteDeadlinkScraper` class:

- `max_pages`: Maximum number of pages to scan (default: 10000)
- `max_depth`: Maximum depth of links to follow from the base URL (default: 20)

## Output

The script generates two CSV files in the Google Drive folder:

1. `deadlinks.csv`: Contains all identified dead links with their source pages.
2. `scan_history.csv`: Keeps track of scanned URLs and their last scan date.

## Limitations

- The script is designed to run in Google Colab for easy Google Drive integration. Modifications may be needed for local use.
- It respects the 'robots.txt' file by default. Ensure you have permission to scan the target website.
- Large websites may take a considerable amount of time to scan completely.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/DrKenReid/website-deadlink-scraper/issues) if you want to contribute.

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is for educational and maintenance purposes only. Always ensure you have permission to scan a website and use this tool responsibly.
