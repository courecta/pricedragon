"""Base spider class for all e-commerce scrapers"""
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from abc import ABC, abstractmethod
import time
import logging
from typing import Dict, List, Optional, Union
import random

class BaseSpider(ABC):
    """Base class for all e-commerce spiders"""
    
    def __init__(self, use_selenium=False, delay_range=(1, 3)):
        self.use_selenium = use_selenium
        self.delay_range = delay_range
        self.session = requests.Session()
        self.driver: Optional[webdriver.Chrome] = None
        
        # Set up headers to avoid bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if self.use_selenium:
            self._setup_selenium()
    
    # Update base_spider.py _setup_selenium method:

    # Replace the _setup_selenium method in base_spider.py:

    def _setup_selenium(self):
        """Setup Selenium WebDriver for dynamic content"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service

            options = Options()

            # Add this to your options
            options.binary_location = "/usr/sbin/chromium"  # or wherever chromium is installed

            # Essential headless options for server environments
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            # options.add_argument('--disable-web-security')
            # options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--window-size=1920,1080')

            # WSL-specific arguments
            options.add_argument('--remote-debugging-port=9222')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            # options.add_argument('--single-process')  # This often helps in WSL

            options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

            print("🚀 Starting Chrome in headless mode with modern ChromeDriver...")

            # Use ChromeDriverManager to handle driver download/setup automatically
            service = Service("/usr/local/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=options)

            # Set timeouts
            self.driver.set_page_load_timeout(15)
            self.driver.implicitly_wait(5)

            print("✅ Modern Selenium Chrome driver initialized successfully")

        except Exception as e:
            print(f"❌ Failed to setup Selenium: {e}")
            print("⚠️ Shopee scraping will be unavailable")
            self.driver = None
    
    def get_page(self, url: str) -> BeautifulSoup:
        """Get page content using requests or selenium"""
        self._random_delay()
        
        if self.use_selenium and self.driver:
            self.driver.get(url)
            html = self.driver.page_source
        else:
            response = self.session.get(url)
            response.raise_for_status()
            html = response.text
        
        return BeautifulSoup(html, 'html.parser')
    
    def _random_delay(self):
        """Add random delay to avoid being blocked"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    @abstractmethod
    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract product information from page"""
        pass
    
    @abstractmethod
    def search_products(self, query: str, max_pages: int = 3) -> List[Dict]:
        """Search for products"""
        pass
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()