#!/usr/bin/env python3
"""
LinkedIn Company Scraper
Usage: python3 linkedin_scraper.py data.csv
"""

import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from urllib.parse import urlparse

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with LinkedIn-friendly settings"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        chrome_options = Options()
        # Don't use headless for LinkedIn to avoid detection
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to look more like a real browser
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Chrome driver initialized for LinkedIn")
            return True
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            self.driver = None
            return False
    
    def extract_followers_count(self, text):
        """Extract followers count from text"""
        # Расширенные паттерны для разных языков
        patterns = [
            # English
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+followers?',
            r'followers?\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # Russian
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+отслеживающих',
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+подписчик',
            r'отслеживающих?\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # German
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+Follower',
            r'Follower\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # French
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+abonnés?',
            r'abonnés?\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # Spanish
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+seguidores?',
            r'seguidores?\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # Portuguese
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+seguidores?',
            
            # Italian
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+follower',
            
            # Dutch
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+volgers?',
            r'volgers?\s*:?\s*([\d\s,.]+(?:\.\d+)?[KMB]?)',
            
            # General patterns
            r'([\d\s,.]+(?:\.\d+)?[KMB]?)\s+(?:followers?|отслеживающих|подписчик|Follower|abonnés?|seguidores?|volgers?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count_str = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
                # Handle K, M, B suffixes
                if count_str.endswith('K'):
                    try:
                        return str(int(float(count_str[:-1]) * 1000))
                    except:
                        continue
                elif count_str.endswith('M'):
                    try:
                        return str(int(float(count_str[:-1]) * 1000000))
                    except:
                        continue
                elif count_str.endswith('B'):
                    try:
                        return str(int(float(count_str[:-1]) * 1000000000))
                    except:
                        continue
                elif count_str.isdigit():
                    return count_str
        
        return None
    

    
    def check_yc_batch_indicator(self, text, batch_name):
        """Check if YC batch indicator is present"""
        # Convert batch name to expected LinkedIn format
        batch_indicators = []
        
        if "Spring 2025" in batch_name:
            batch_indicators = ["X25", "Spring 2025", "YC X25", "YC Spring 2025", "Spring '25"]
        elif "Summer 2025" in batch_name:
            batch_indicators = ["S25", "Summer 2025", "YC S25", "YC Summer 2025", "Summer '25"]
        elif "Winter 2025" in batch_name:
            batch_indicators = ["W25", "Winter 2025", "YC W25", "YC Winter 2025", "Winter '25"]
        
        # Check if any indicator is present in the text
        for indicator in batch_indicators:
            if indicator.lower() in text.lower():
                return True
        
        return False
    
    def scrape_linkedin_company(self, linkedin_url, batch_name, max_retries=2):
        """Scrape LinkedIn company page"""
        if not linkedin_url or pd.isna(linkedin_url) or linkedin_url == '':
            return {
                'linkedin_url': '',
                'followers_count': None,
                'has_yc_batch_indicator': False,
                'error': 'No LinkedIn URL provided'
            }
        
        # Clean URL
        if not linkedin_url.startswith('http'):
            linkedin_url = f"https://{linkedin_url}"
        
        company_name = linkedin_url.split('/company/')[-1].split('/')[0] if '/company/' in linkedin_url else 'unknown'
        
        for attempt in range(max_retries):
            print(f"   🔍 Processing LinkedIn: {company_name} (attempt {attempt + 1}/{max_retries})")
            
            if not self.setup_driver():
                continue
            
            try:
                # Load LinkedIn page
                self.driver.get(linkedin_url)
                time.sleep(8)  # Wait for page to load
                
                # Get page source for analysis
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Initialize results
                result = {
                    'linkedin_url': linkedin_url,
                    'followers_count': None,
                    'has_yc_batch_indicator': False,
                    'error': None
                }
                
                # Check if page loaded properly (not blocked or error)
                if "Page not found" in page_text or "This page doesn't exist" in page_text:
                    result['error'] = 'Page not found'
                    return result
                
                if "Sign in" in page_text and "to see more" in page_text:
                    print(f"   ⚠️  LinkedIn requires sign-in, extracting available data...")
                
                # Extract followers count
                followers = self.extract_followers_count(page_text)
                if followers:
                    result['followers_count'] = followers
                    print(f"   📊 Followers: {followers}")
                
                # Skip employee extraction - removed as requested
                
                # Check for YC batch indicator
                has_indicator = self.check_yc_batch_indicator(page_text, batch_name)
                result['has_yc_batch_indicator'] = has_indicator
                if has_indicator:
                    print(f"   🚀 YC batch indicator found!")
                
                print(f"   ✅ SUCCESS: Extracted LinkedIn data")
                return result
                
            except Exception as e:
                print(f"   ❌ Error on attempt {attempt + 1}: {str(e)[:50]}...")
                if attempt == max_retries - 1:
                    return {
                        'linkedin_url': linkedin_url,
                        'followers_count': None,
                        'has_yc_batch_indicator': False,
                        'error': str(e)[:100]
                    }
            
            finally:
                if self.driver:
                    self.driver.quit()
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        return {
            'linkedin_url': linkedin_url,
            'followers_count': None,
            'has_yc_batch_indicator': False,
            'error': 'All attempts failed'
        }
    
    def scrape_companies_linkedin(self, csv_file):
        """Scrape LinkedIn data for all companies in CSV"""
        print(f"🚀 Starting LinkedIn scraping from {csv_file}...")
        
        # Load data
        try:
            df = pd.read_csv(csv_file)
        except FileNotFoundError:
            print(f"❌ File {csv_file} not found")
            return
        
        if 'Linkedin Link' not in df.columns:
            print("❌ 'Linkedin Link' column not found in CSV")
            return
        
        # Filter companies with LinkedIn URLs
        linkedin_companies = df[df['Linkedin Link'].notna() & (df['Linkedin Link'] != '')].copy()
        print(f"📊 Found {len(linkedin_companies)} companies with LinkedIn URLs")
        
        if linkedin_companies.empty:
            print("❌ No companies with LinkedIn URLs found")
            return
        
        # Prepare results
        results = []
        
        # Process each company
        for i, (idx, company) in enumerate(linkedin_companies.iterrows()):
            print(f"\n🔍 Processing {i+1}/{len(linkedin_companies)}")
            print(f"   Company: {company['Title']}")
            print(f"   Batch: {company['Batch']}")
            print(f"   LinkedIn: {company['Linkedin Link']}")
            
            # Scrape LinkedIn data
            linkedin_data = self.scrape_linkedin_company(
                company['Linkedin Link'], 
                company['Batch']
            )
            
            # Combine with original data
            result = {
                'Original_Index': idx,
                'Batch': company['Batch'],
                'Title': company['Title'],
                'LinkedIn_URL': linkedin_data['linkedin_url'],
                'Followers_Count': linkedin_data['followers_count'],
                'Has_YC_Batch_Indicator': linkedin_data['has_yc_batch_indicator'],
                'Error': linkedin_data['error']
            }
            
            results.append(result)
            
            # Print results
            print(f"   📊 Results:")
            print(f"      Followers: {result['Followers_Count']}")
            print(f"      YC Indicator: {result['Has_YC_Batch_Indicator']}")
            if result['Error']:
                print(f"      Error: {result['Error']}")
            
            # Save intermediate results every 10 companies
            if (i + 1) % 10 == 0:
                print(f"💾 Saving intermediate results...")
                temp_df = pd.DataFrame(results)
                temp_df.to_csv(f'linkedin_data_partial_{i+1}.csv', index=False)
                print(f"   Saved {len(results)} companies to partial file")
            
            # Delay between requests to be respectful
            time.sleep(3)
        
        # Save final results
        results_df = pd.DataFrame(results)
        output_file = 'linkedin_company_data.csv'
        results_df.to_csv(output_file, index=False)
        
        print(f"\n✅ LinkedIn scraping completed!")
        print(f"📁 Results saved to: {output_file}")
        
        # Statistics
        total_companies = len(results_df)
        with_followers = len(results_df[results_df['Followers_Count'].notna()])
        with_yc_indicator = len(results_df[results_df['Has_YC_Batch_Indicator'] == True])
        with_errors = len(results_df[results_df['Error'].notna()])
        
        print(f"\n📈 Statistics:")
        print(f"   Total companies processed: {total_companies}")
        print(f"   With followers data: {with_followers} ({with_followers/total_companies*100:.1f}%)")
        print(f"   With YC batch indicator: {with_yc_indicator} ({with_yc_indicator/total_companies*100:.1f}%)")
        print(f"   With errors: {with_errors} ({with_errors/total_companies*100:.1f}%)")
        
        return results_df

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 linkedin_scraper.py <csv_file>")
        print("Example: python3 linkedin_scraper.py data.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    scraper = LinkedInScraper()
    results = scraper.scrape_companies_linkedin(csv_file)
    
    if results is not None:
        print(f"\n🎉 SUCCESS! Scraped LinkedIn data for {len(results)} companies!")
    else:
        print("❌ LinkedIn scraping failed")

if __name__ == "__main__":
    main()