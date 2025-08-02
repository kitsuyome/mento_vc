#!/usr/bin/env python3
"""
Universal YC Company Scraper
Usage: python3 yc_scraper.py "Summer 2025"
       python3 yc_scraper.py "Spring 2025"
       python3 yc_scraper.py "Winter 2025"
"""

import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re

class YCScraperUniversal:
    def __init__(self, batch_name):
        self.batch_name = batch_name
        self.driver = None
        self.base_url = "https://www.ycombinator.com"
        self.companies_url = "https://www.ycombinator.com/companies"
        
    def setup_driver(self):
        """Setup fresh Chrome driver with extended timeouts"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(10)
            
            # Hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Fresh Chrome driver initialized")
            return True
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            self.driver = None
            return False
    
    def get_all_company_urls(self):
        """Get all company URLs for the specified batch"""
        if not self.setup_driver():
            return []
        
        try:
            print(f"🌐 Loading YC companies page...")
            self.driver.get(self.companies_url)
            time.sleep(5)
            
            # Click batch filter
            print(f"🔍 Looking for {self.batch_name} filter...")
            batch_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{self.batch_name}')]")
            
            if batch_elements:
                batch_elements[0].click()
                print(f"✅ Clicked {self.batch_name} filter")
                time.sleep(3)
            else:
                print(f"❌ {self.batch_name} filter not found")
                return []
            
            # Scroll to load all companies
            print("📜 Scrolling to load all companies...")
            last_count = 0
            scroll_attempts = 0
            max_scrolls = 50
            
            while scroll_attempts < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                current_links = self.driver.find_elements(By.CSS_SELECTOR, "a._company_i9oky_355")
                current_count = len(current_links)
                
                if current_count == last_count:
                    break
                
                last_count = current_count
                scroll_attempts += 1
                
                if scroll_attempts % 10 == 0:
                    print(f"   Scroll {scroll_attempts}: {current_count} companies found")
            
            print(f"🎯 Found {last_count} total companies")
            
            # Get all company URLs
            company_links = self.driver.find_elements(By.CSS_SELECTOR, "a._company_i9oky_355")
            company_urls = []
            
            for link in company_links:
                href = link.get_attribute('href')
                if href and '/companies/' in href and 'founders' not in href:
                    company_urls.append(href)
            
            print(f"📋 Extracted {len(company_urls)} company URLs")
            return company_urls
            
        except Exception as e:
            print(f"❌ Error getting company URLs: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def extract_company_details_with_retry(self, company_url: str, max_retries=3):
        """Extract company details with retry logic"""
        company_name = company_url.split('/companies/')[-1]
        
        for attempt in range(max_retries):
            print(f"   🔍 Processing: {company_name} (attempt {attempt + 1}/{max_retries})")
            
            # Setup fresh driver for each attempt
            if not self.setup_driver():
                continue
            
            try:
                # Load the company page
                self.driver.get(company_url)
                time.sleep(5)
                
                # Initialize data
                data = {
                    'title': '',
                    'short_description': '',
                    'tags': '',
                    'founded': '',
                    'team_size': '',
                    'location': '',
                    'jobs': '',
                    'company_link': '',
                    'linkedin_link': '',
                    'primary_partner': '',
                    'long_description': '',
                    'yc_page': company_url
                }
                
                # Check if page loaded properly
                try:
                    self.driver.implicitly_wait(15)
                    page_source = self.driver.page_source
                    if "404" in self.driver.title or len(page_source) < 1000:
                        print(f"   ⚠️  Page seems incomplete, retrying...")
                        continue
                except:
                    print(f"   ⚠️  Page load issue, retrying...")
                    continue
                
                # 1. Title
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, "h1.text-3xl.font-bold")
                    data['title'] = title_elem.text.strip()
                except:
                    try:
                        title_elem = self.driver.find_element(By.TAG_NAME, "h1")
                        data['title'] = title_elem.text.strip()
                    except:
                        data['title'] = company_name.replace('-', ' ').title()
                
                # 2. Short Description
                try:
                    meta_desc = self.driver.find_element(By.CSS_SELECTOR, "meta[name='description']")
                    data['short_description'] = meta_desc.get_attribute('content')
                except:
                    try:
                        desc_elem = self.driver.find_element(By.CSS_SELECTOR, "div.text-xl")
                        data['short_description'] = desc_elem.text.strip()
                    except:
                        pass
                
                # 3. Tags
                try:
                    main_container = self.driver.find_element(By.CSS_SELECTOR, "div.flex.flex-col.gap-8")
                    container_text = main_container.text
                    
                    lines = container_text.split('\n')
                    tags = []
                    
                    for line in lines:
                        line = line.strip()
                        if line.isupper() and len(line) > 1 and len(line) < 30:
                            if line not in ['SPRING 2025', 'WINTER 2025', 'SUMMER 2025', 'ACTIVE', 'INACTIVE']:
                                if not any(city in line for city in ['NEW YORK', 'SAN FRANCISCO', 'LOS ANGELES', 'CHICAGO', 'BOSTON', 'SEATTLE']):
                                    tags.append(line)
                    
                    data['tags'] = ', '.join(tags)
                except:
                    pass
                
                # 4. Founded
                try:
                    founded_span = self.driver.find_element(By.XPATH, "//span[text()='Founded:']")
                    parent = founded_span.find_element(By.XPATH, "..")
                    founded_text = parent.text
                    year_match = re.search(r'(\d{4})', founded_text)
                    if year_match:
                        data['founded'] = year_match.group(1)
                except:
                    pass
                
                # 5. Team Size
                try:
                    team_span = self.driver.find_element(By.XPATH, "//span[text()='Team Size:']")
                    parent = team_span.find_element(By.XPATH, "..")
                    team_text = parent.text
                    size_match = re.search(r'(\d+)', team_text)
                    if size_match:
                        data['team_size'] = size_match.group(1)
                except:
                    pass
                
                # 6. Location
                try:
                    location_span = self.driver.find_element(By.XPATH, "//span[text()='Location:']")
                    parent = location_span.find_element(By.XPATH, "..")
                    location_text = parent.text
                    location_lines = location_text.split('\n')
                    if len(location_lines) > 1:
                        data['location'] = location_lines[1].strip()
                except:
                    try:
                        main_container = self.driver.find_element(By.CSS_SELECTOR, "div.flex.flex-col.gap-8")
                        container_text = main_container.text
                        cities = ['NEW YORK', 'SAN FRANCISCO', 'LOS ANGELES', 'CHICAGO', 'BOSTON', 'SEATTLE', 'AUSTIN', 'DENVER', 'MIAMI']
                        for city in cities:
                            if city in container_text:
                                data['location'] = city.title()
                                break
                    except:
                        pass
                
                # 7. Jobs
                try:
                    main_container = self.driver.find_element(By.CSS_SELECTOR, "div.flex.flex-col.gap-8")
                    container_text = main_container.text
                    lines = container_text.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip() == 'Jobs' and i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line.isdigit():
                                data['jobs'] = next_line
                                break
                except:
                    pass
                
                # 8. Company Link
                try:
                    website_div = self.driver.find_element(By.CSS_SELECTOR, "div.inline-block.group-hover\\:underline")
                    website_text = website_div.text.strip()
                    if website_text.startswith('http'):
                        data['company_link'] = website_text
                    else:
                        data['company_link'] = f"https://{website_text}"
                except:
                    try:
                        all_links = self.driver.find_elements(By.TAG_NAME, "a")
                        for link in all_links:
                            href = link.get_attribute('href')
                            if href and href.startswith('http'):
                                if not any(domain in href for domain in ['ycombinator.com', 'twitter.com', 'linkedin.com', 'facebook.com', 'startupschool.org']):
                                    data['company_link'] = href
                                    break
                    except:
                        pass
                
                # 9. LinkedIn Link
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        href = link.get_attribute('href')
                        if href and 'linkedin.com/company/' in href:
                            data['linkedin_link'] = href
                            break
                except:
                    pass
                
                # 10. Primary Partner
                try:
                    partner_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Partner')]")
                    for elem in partner_elements[:3]:
                        text = elem.text
                        if 'Primary Partner' in text or 'Partner:' in text:
                            lines = text.split('\n')
                            for line in lines:
                                if 'Partner' in line and ':' in line:
                                    partner = line.split(':')[-1].strip()
                                    if len(partner) > 2 and len(partner) < 50:
                                        data['primary_partner'] = partner
                                        break
                            break
                except:
                    pass
                
                # 11. Long Description
                try:
                    prose_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.prose")
                    for prose in prose_elements:
                        text = prose.text.strip()
                        if len(text) > 100 and any(keyword in text.lower() for keyword in ['helps', 'platform', 'service', 'business', 'solution']):
                            data['long_description'] = text
                            break
                except:
                    pass
                
                # Check if we got meaningful data
                if data['title'] and (data['short_description'] or data['company_link']):
                    print(f"   ✅ SUCCESS on attempt {attempt + 1}")
                    return data
                else:
                    print(f"   ⚠️  Incomplete data on attempt {attempt + 1}, retrying...")
                    
            except Exception as e:
                print(f"   ❌ Error on attempt {attempt + 1}: {str(e)[:50]}...")
                
            finally:
                if self.driver:
                    self.driver.quit()
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        # If all attempts failed
        print(f"   ❌ All {max_retries} attempts failed")
        return None
    
    def scrape_batch(self):
        """Scrape all companies for the specified batch"""
        print(f"🚀 Starting {self.batch_name} scraping...")
        print("🔧 Using extended timeouts and retry logic")
        
        # First, get all company URLs
        company_urls = self.get_all_company_urls()
        
        if not company_urls:
            print("❌ No company URLs found")
            return []
        
        companies = []
        
        # Process each company with retry logic
        for i, url in enumerate(company_urls):
            print(f"\n🔍 Processing {i+1}/{len(company_urls)}")
            
            details = self.extract_company_details_with_retry(url)
            
            if details:
                companies.append({
                    'Batch': self.batch_name,
                    'Title': details['title'],
                    'Short Description': details['short_description'],
                    'Tags': details['tags'],
                    'Founded': details['founded'],
                    'Team Size': details['team_size'],
                    'Location': details['location'],
                    'Jobs': details['jobs'],
                    'Company Link': details['company_link'],
                    'Linkedin Link': details['linkedin_link'],
                    'Primary Partner': details['primary_partner'],
                    'Long Description': details['long_description'],
                    'YC Page': details['yc_page']
                })
                
                # Print detailed output
                print(f"   ✅ EXTRACTED DATA:")
                print(f"      Batch: {self.batch_name}")
                print(f"      Title: {details['title']}")
                print(f"      Short Description: {details['short_description'][:100]}..." if details['short_description'] else "      Short Description: (empty)")
                print(f"      Tags: {details['tags']}")
                print(f"      Founded: {details['founded']}")
                print(f"      Team Size: {details['team_size']}")
                print(f"      Location: {details['location']}")
                print(f"      Jobs: {details['jobs']}")
                print(f"      Company Link: {details['company_link']}")
                print(f"      Linkedin Link: {details['linkedin_link']}")
                print(f"      Primary Partner: {details['primary_partner']}")
                print(f"      Long Description: {details['long_description'][:100]}..." if details['long_description'] else "      Long Description: (empty)")
                print(f"      YC Page: {details['yc_page']}")
            else:
                print(f"   ❌ Failed to extract data after all retries")
                company_name = url.split('/companies/')[-1]
                companies.append({
                    'Batch': self.batch_name,
                    'Title': company_name.replace('-', ' ').title(),
                    'Short Description': '',
                    'Tags': '',
                    'Founded': '',
                    'Team Size': '',
                    'Location': '',
                    'Jobs': '',
                    'Company Link': '',
                    'Linkedin Link': '',
                    'Primary Partner': '',
                    'Long Description': '',
                    'YC Page': url
                })
            
            # Progress updates
            if (i + 1) % 10 == 0:
                successful = len([c for c in companies if c['Short Description'] != ''])
                print(f"\n📊 Progress: {i + 1}/{len(company_urls)} companies processed")
                print(f"   Successful extractions: {successful}")
            
            # Save intermediate results every 20 companies
            if (i + 1) % 20 == 0:
                print(f"💾 Saving intermediate results...")
                temp_df = pd.DataFrame(companies)
                batch_safe = self.batch_name.lower().replace(' ', '_')
                temp_df.to_csv(f'yc_{batch_safe}_partial_{i+1}.csv', index=False)
                print(f"   Saved {len(companies)} companies to partial file")
            
            # Small delay between companies
            time.sleep(1)
        
        return companies
    
    def save_to_csv(self, companies, filename=None):
        """Save companies to CSV"""
        if not companies:
            print("❌ No companies to save")
            return
        
        if filename is None:
            batch_safe = self.batch_name.lower().replace(' ', '_')
            filename = f'yc_{batch_safe}_companies.csv'
        
        df = pd.DataFrame(companies)
        
        required_columns = [
            'Batch', 'Title', 'Short Description', 'Tags', 'Founded', 
            'Team Size', 'Location', 'Jobs', 'Company Link', 
            'Linkedin Link', 'Primary Partner', 'Long Description', 'YC Page'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[required_columns]
        df = df.drop_duplicates(subset=['Title'], keep='first')
        
        df.to_csv(filename, index=False)
        
        print(f"✅ Saved {len(df)} companies to {filename}")
        
        # Stats
        stats = {
            'Total companies': len(df),
            'With websites': len(df[df['Company Link'] != '']),
            'With LinkedIn': len(df[df['Linkedin Link'] != '']),
            'With descriptions': len(df[df['Short Description'] != '']),
            'With tags': len(df[df['Tags'] != '']),
            'With founded year': len(df[df['Founded'] != '']),
            'With team size': len(df[df['Team Size'] != '']),
            'With location': len(df[df['Location'] != '']),
            'With jobs count': len(df[df['Jobs'] != ''])
        }
        
        print(f"\n📈 Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        return filename

def main():
    parser = argparse.ArgumentParser(description='Universal YC Company Scraper')
    parser.add_argument('batch', help='Batch name (e.g., "Summer 2025", "Spring 2025", "Winter 2025")')
    parser.add_argument('--output', '-o', help='Output CSV filename (optional)')
    
    args = parser.parse_args()
    
    scraper = YCScraperUniversal(args.batch)
    companies = scraper.scrape_batch()
    
    if companies:
        filename = scraper.save_to_csv(companies, args.output)
        print(f"\n🎉 SUCCESS! Scraped {len(companies)} {args.batch} companies!")
        print(f"📁 Data saved to: {filename}")
    else:
        print("❌ No companies scraped")

if __name__ == "__main__":
    main()