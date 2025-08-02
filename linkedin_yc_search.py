#!/usr/bin/env python3
"""
LinkedIn Multi-Page Search with Manual Authorization
Searches through all 10 pages of YC S25 results
Usage: python3 linkedin_multi_page.py
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

class LinkedInMultiPageSearch:
    def __init__(self):
        self.driver = None
        self.base_search_url = "https://www.linkedin.com/search/results/companies/?keywords=YC%20S25"
        self.all_companies = set()
        
    def setup_driver(self):
        """Setup Chrome driver with enhanced settings for LinkedIn"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # CRITICAL: Keep browser window active and focused
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # Enhanced user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional options for better LinkedIn compatibility
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        # DON'T disable images - LinkedIn needs them for lazy loading detection
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(45)
            self.driver.implicitly_wait(10)
            
            # CRITICAL: Maximize window and bring to front
            self.driver.maximize_window()
            
            # Hide automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Keep page active and prevent throttling
            self.driver.execute_script("""
                // Prevent page from being throttled
                Object.defineProperty(document, 'hidden', {value: false, writable: false});
                Object.defineProperty(document, 'visibilityState', {value: 'visible', writable: false});
                
                // Override page visibility API
                document.addEventListener('visibilitychange', function(e) {
                    e.stopImmediatePropagation();
                }, true);
                
                // Keep page "active"
                setInterval(function() {
                    document.dispatchEvent(new Event('mousemove'));
                    document.dispatchEvent(new Event('keypress'));
                }, 1000);
            """)
            
            print("✅ Chrome driver initialized with ACTIVE WINDOW settings")
            return True
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            return False
    
    def login_to_linkedin(self):
        """Handle LinkedIn login"""
        print("🌐 Opening LinkedIn...")
        self.driver.get("https://www.linkedin.com")
        time.sleep(3)
        
        print("\n" + "="*60)
        print("🔐 MANUAL AUTHORIZATION REQUIRED")
        print("="*60)
        print("1. A browser window should have opened")
        print("2. Please log in to LinkedIn manually")
        print("3. Once logged in, press Enter here to continue")
        print("="*60)
        
        input("Press Enter after you've logged in to LinkedIn...")
    
    def search_page(self, page_num):
        """Search a specific page with smart LinkedIn scrolling"""
        page_url = f"{self.base_search_url}&page={page_num}"
        
        print(f"\n📄 Processing page {page_num}...")
        print(f"🔗 URL: {page_url}")
        
        try:
            self.driver.get(page_url)
            
            # Wait for initial page load
            print("⏳ Waiting for LinkedIn page to load...")
            time.sleep(8)
            
            # Wait for content to appear
            try:
                wait = WebDriverWait(self.driver, 15)
                wait.until(lambda driver: len(driver.find_element(By.TAG_NAME, "body").text) > 1000)
                print("✅ Page content loaded")
            except Exception as e:
                print(f"⚠️ Timeout waiting for content: {e}")
            
            print("SCROLLING")
            
            # CRITICAL: Ensure window stays active and focused
            self.driver.switch_to.window(self.driver.current_window_handle)
            
            # Keep simulating user activity
            self.driver.execute_script("""
                // Simulate active user
                window.isActive = true;
                window.focus();
                
                // Continuous activity simulation
                window.activityInterval = setInterval(function() {
                    // Simulate mouse movement
                    document.dispatchEvent(new MouseEvent('mousemove', {
                        clientX: Math.random() * window.innerWidth,
                        clientY: Math.random() * window.innerHeight
                    }));
                    
                    // Simulate key activity
                    document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowDown'}));
                    
                    // Keep focus
                    window.focus();
                }, 500);
            """)
            
            # Start from top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(3)
            
            # Get initial count
            initial_text = self.driver.find_element(By.TAG_NAME, "body").text
            initial_count = initial_text.count('(YC S25)')
            print(f"   Initial YC S25 count: {initial_count}")
            
            # EXTREME SCROLLING LOOP
            for scroll_round in range(20):  # 20 rounds of scrolling
                print(f"   🔄 Scroll round {scroll_round + 1}/20")
                
                # Get current height
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Scroll in 10 steps from top to bottom with activity simulation
                for step in range(10):
                    scroll_position = (step + 1) * (current_height / 10)
                    
                    # Keep window active while scrolling
                    self.driver.execute_script(f"""
                        // Keep window focused and active
                        window.focus();
                        
                        // Scroll to position
                        window.scrollTo(0, {scroll_position});
                        
                        // Simulate user interaction
                        document.dispatchEvent(new MouseEvent('mousemove', {{
                            clientX: {100 + step * 10},
                            clientY: {100 + step * 10}
                        }}));
                        
                        // Force scroll events
                        window.dispatchEvent(new Event('scroll'));
                    """)
                    time.sleep(2)  # Longer wait for LinkedIn to process
                
                # Scroll to absolute bottom multiple times with activity
                for bottom_scroll in range(5):
                    self.driver.execute_script("""
                        // Keep window active and focused
                        window.focus();
                        
                        // Scroll to bottom
                        window.scrollTo(0, document.body.scrollHeight);
                        document.body.scrollTop = document.body.scrollHeight;
                        document.documentElement.scrollTop = document.body.scrollHeight;
                        
                        // Simulate user activity
                        document.dispatchEvent(new MouseEvent('mousemove', {
                            clientX: Math.random() * 200 + 100,
                            clientY: Math.random() * 200 + 100
                        }));
                        
                        // Force all scroll events
                        window.dispatchEvent(new Event('scroll'));
                        window.dispatchEvent(new Event('wheel'));
                        window.dispatchEvent(new Event('touchmove'));
                    """)
                    time.sleep(3)  # Longer wait for LinkedIn
                
                # Check if we found more companies
                current_text = self.driver.find_element(By.TAG_NAME, "body").text
                current_count = current_text.count('(YC S25)')
                print(f"   After round {scroll_round + 1}: {current_count} YC S25 mentions")
                
                # If we found 10+ companies, we're good
                if current_count >= 10:
                    print(f"   🎯 SUCCESS! Found {current_count} YC mentions!")
                    break
                    
                # If no progress for several rounds, try different approach
                if scroll_round > 5 and current_count == initial_count:
                    print(f"   ⚠️ No progress, trying page refresh approach...")
                    # Refresh and try again
                    self.driver.refresh()
                    time.sleep(8)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
            
            # FINAL DESPERATE MEASURES
            print("🔄 Final desperate scrolling...")
            for desperate in range(15):
                # Multiple scroll techniques simultaneously
                self.driver.execute_script("""
                    // Scroll to bottom
                    window.scrollTo(0, document.body.scrollHeight);
                    
                    // Force all scroll events
                    window.dispatchEvent(new Event('scroll'));
                    window.dispatchEvent(new Event('wheel'));
                    window.dispatchEvent(new Event('touchmove'));
                    window.dispatchEvent(new Event('resize'));
                    
                    // Set scroll position directly
                    document.body.scrollTop = document.body.scrollHeight;
                    document.documentElement.scrollTop = document.body.scrollHeight;
                """)
                time.sleep(3)
            
            print("✅ Nuclear scrolling complete!")
            
            # Try to click any "Show more" or "Load more" buttons
            try:
                show_more_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Show more') or contains(text(), 'Load more') or contains(text(), 'See more')]")
                for button in show_more_buttons:
                    try:
                        self.driver.execute_script("arguments[0].click();", button)
                        print("   🔘 Clicked 'Show more' button")
                        time.sleep(3)
                    except:
                        pass
            except:
                pass
            
            # Extract final results
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            final_yc_count = page_text.count('(YC S25)')
            print(f"📊 FINAL RESULT: Found {final_yc_count} YC S25 mentions on page")
            page_companies = self.extract_companies_from_text(page_text, page_num)
            
            # Get LinkedIn URLs
            linkedin_urls = self.get_linkedin_url_from_current_page()
            
            # Combine company names with URLs
            companies_with_urls = []
            for company_name in page_companies:
                linkedin_url = ''
                # Try to match company name with LinkedIn URL
                for link_text, url in linkedin_urls.items():
                    if company_name.lower() in link_text.lower() or link_text.lower() in company_name.lower():
                        linkedin_url = url
                        break
                
                companies_with_urls.append({
                    'title': company_name,
                    'linkedin_url': linkedin_url
                })
            
            print(f"✅ Page {page_num} complete: {len(companies_with_urls)} companies extracted")
            return companies_with_urls
                
        except Exception as e:
            print(f"❌ Error processing page {page_num}: {e}")
            return []
    
    def extract_companies_from_text(self, page_text, page_num):
        """Extract companies with exact (YC S25) pattern"""
        print(f"🔍 Extracting YC S25 companies from page {page_num}...")
        
        page_companies = set()
        
        # Debug: Show ALL YC S25 contexts to understand the pattern
        yc_contexts = []
        for match in re.finditer(r'.{0,80}\(YC S25\).{0,10}', page_text, re.IGNORECASE):
            context = match.group().strip()
            yc_contexts.append(context)
        
        print(f"   🔍 Found {len(yc_contexts)} YC S25 contexts")
        if yc_contexts:
            print("   📝 ALL contexts found:")
            for i, context in enumerate(yc_contexts):
                print(f"      {i+1}. {context}")
        
        # SIMPLE extraction - just remove (YC S25) from each context
        all_matches = set()
        
        for context in yc_contexts:
            # Simply remove (YC S25) and clean up the remaining text
            company_name = context.replace('(YC S25)', '').strip()
            
            # Basic cleaning
            company_name = re.sub(r'\s+', ' ', company_name)  # Normalize spaces
            company_name = company_name.strip()
            
            # Remove any trailing/leading punctuation
            company_name = re.sub(r'^[^\w]+|[^\w]+$', '', company_name)
            
            if company_name and len(company_name) >= 2:
                all_matches.add(company_name)
                print(f"      🎯 Extracted: '{company_name}' from context: {context[:60]}...")
        
        print(f"   🔍 Found {len(all_matches)} potential matches after extraction")
        
        # Validate each match with simpler validation
        for i, match in enumerate(sorted(all_matches)):
            # Simple validation - just check it's not obvious junk
            if (len(match) >= 2 and 
                re.search(r'[A-Za-z]', match) and 
                not re.match(r'^\d+$', match) and
                'result' not in match.lower() and
                'page' not in match.lower() and
                'follow' not in match.lower()):
                
                page_companies.add(match)
                print(f"      ✅ {len(page_companies)}. {match}")
            else:
                print(f"      ❌ Rejected: {match}")
        
        print(f"📊 Page {page_num}: {len(page_companies)} valid companies found")
        
        # Add to global set
        self.all_companies.update(page_companies)
        
        return list(page_companies)
    
    def clean_company_name(self, name):
        """Clean and normalize company name"""
        if not name:
            return None
            
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common LinkedIn prefixes/suffixes that get captured
        prefixes_to_remove = [
            r'^.*?page\s+\d+\s+of\s+\d+\s+search\s+result\s+pages\.\s*\d+\s+results\s+',
            r'^.*?followers?\s+',
            r'^.*?\d+K?\s+followers?\s+',
            r'^.*?Visit\s+website\s+',
            r'^.*?Follow\s+',
        ]
        
        for prefix in prefixes_to_remove:
            name = re.sub(prefix, '', name, flags=re.IGNORECASE)
        
        # Remove trailing junk
        suffixes_to_remove = [
            r'\s+Follow$',
            r'\s+Visit\s+website$',
            r'\s+\d+K?\s+followers?.*$',
            r'\s+\d+\s+jobs?.*$',
        ]
        
        for suffix in suffixes_to_remove:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation
        name = re.sub(r'[.,;:!?]+$', '', name)
        
        # Final cleanup - remove any remaining numbers at start/end
        name = re.sub(r'^\d+\s+', '', name)
        name = re.sub(r'\s+\d+$', '', name)
        
        return name.strip() if name.strip() else None
    
    def validate_company_name(self, name):
        """Validate if this looks like a real company name"""
        if not name:
            return False
            
        # Check length - company names should be reasonable
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Must contain at least one letter
        if not re.search(r'[A-Za-z]', name):
            return False
        
        # Exclude LinkedIn UI junk and common false positives
        invalid_patterns = [
            r'^(follow|unfollow|followers|results|search|page|next|previous|visit|website)$',
            r'^\d+\s*(followers|results|jobs|K|k|pages?)\s*$',
            r'^[0-9\s,.-]+$',
            r'^\W+$',
            r'^(linkedin|facebook|twitter|instagram)\.com',
            r'^(the|a|an|and|or|but|in|on|at|to|for|of|with|by)$',
            r'search\s+result',
            r'page\s+\d+',
            r'^\d+\s+of\s+\d+',
            r'changing\s+the\s+way',
            r'interactive\s+tutor',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Should look like a company name (starts with capital letter or number)
        if not re.match(r'^[A-Z0-9]', name):
            return False
        
        return True
    
    def search_all_pages(self):
        """Search all pages efficiently"""
        print("🔍 Starting multi-page LinkedIn search...")
        
        if not self.setup_driver():
            return []
        
        try:
            # Login first
            self.login_to_linkedin()
            
            all_found_companies = []
            
            # Search pages 1-10 (typical LinkedIn search result pages)
            for page_num in range(1, 11):
                try:
                    print(f"\n{'='*50}")
                    print(f"🔄 PROCESSING PAGE {page_num}")
                    print(f"{'='*50}")
                    
                    # Wait between pages to avoid rate limiting
                    if page_num > 1:
                        print("⏳ Waiting between pages...")
                        time.sleep(5)
                    
                    page_companies = self.search_page(page_num)
                    
                    if not page_companies:
                        print(f"⚠️ No companies found on page {page_num}")
                        # Continue to next page instead of stopping
                        continue
                    else:
                        all_found_companies.extend(page_companies)
                        print(f"✅ Page {page_num}: Added {len(page_companies)} companies")
                    
                    # Show running total
                    total_unique = len(self.all_companies)
                    print(f"📊 Running total: {total_unique} unique companies found")
                        
                except Exception as e:
                    print(f"❌ Error on page {page_num}: {e}")
                    # Continue to next page
                    continue
            
            # Process results
            companies = []
            for company_data in all_found_companies:
                if isinstance(company_data, dict):
                    companies.append(company_data)
                else:
                    companies.append({
                        'title': company_data,
                        'linkedin_url': ''
                    })
            
            print(f"\n🎉 SEARCH COMPLETE!")
            print(f"📊 Total unique companies found: {len(companies)}")
            print(f"📄 Successfully searched 10 pages")
            
            if companies:
                print(f"🔍 Sample companies found:")
                for i, company in enumerate(companies[:10]):
                    print(f"   {i+1}. {company['title']}")
                if len(companies) > 10:
                    print(f"   ... and {len(companies) - 10} more")
                
                # Сохранить результаты в data.csv
                self.save_results(companies)
            
            return companies
            
        except Exception as e:
            print(f"❌ Error during multi-page search: {e}")
            return []
        
        finally:
            if self.driver:
                print("\n" + "="*60)
                print("🔍 MULTI-PAGE SEARCH COMPLETE")
                print("="*60)
                print("Please review the results above")
                input("Press Enter to close browser...")
                self.driver.quit()
    
    def get_linkedin_url_from_current_page(self):
        """Extract LinkedIn company URLs from current page"""
        try:
            # Найти все ссылки на компании LinkedIn
            company_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/company/']")
            
            company_urls = {}
            for link in company_links:
                href = link.get_attribute('href')
                if href and '/company/' in href and 'linkedin.com' in href:
                    # Получить текст ссылки для сопоставления с названием компании
                    link_text = link.text.strip()
                    if link_text:
                        company_urls[link_text] = href
            
            return company_urls
        except Exception as e:
            print(f"   ⚠️ Error extracting LinkedIn URLs: {e}")
            return {}
    
    def save_results(self, companies):
        """Save found companies to data.csv with duplicate checking"""
        if not companies:
            print("❌ No companies found to save")
            return
        
        print(f"\n💾 Processing {len(companies)} found companies...")
        
        # Загрузить существующие данные
        existing_companies = set()
        existing_links = set()
        
        try:
            df = pd.read_csv('data.csv')
            for _, row in df.iterrows():
                if pd.notna(row['Title']):
                    existing_companies.add(row['Title'].strip().lower())
                if pd.notna(row['Linkedin Link']) and row['Linkedin Link'].strip():
                    existing_links.add(row['Linkedin Link'].strip().lower())
            print(f"📊 Loaded {len(existing_companies)} existing companies")
        except FileNotFoundError:
            df = pd.DataFrame()
            print("⚠️ data.csv not found, will create new file")
        
        # Фильтровать дубликаты по названию И ссылке (регистронезависимо)
        new_companies = []
        for company in companies:
            title_lower = company['title'].strip().lower()
            link_lower = company.get('linkedin_url', '').strip().lower()
            
            # Проверяем дубликаты по названию ИЛИ по ссылке LinkedIn
            is_duplicate_title = title_lower in existing_companies
            is_duplicate_link = link_lower and link_lower in existing_links
            
            if not is_duplicate_title and not is_duplicate_link:
                new_companies.append(company)
                print(f"   ✅ New: {company['title']}")
            else:
                if is_duplicate_title:
                    print(f"   🔄 Duplicate title: {company['title']}")
                if is_duplicate_link:
                    print(f"   🔄 Duplicate LinkedIn: {company['title']}")
        
        if not new_companies:
            print("❌ No new companies to add")
            return
        
        # Конвертировать в DataFrame с правильной структурой
        new_data = []
        for company in new_companies:
            new_data.append({
                'Batch': 'Summer 2025',
                'Title': company['title'],
                'Short Description': '',  # Пустое поле
                'Tags': '',              # Пустое поле
                'Founded': '',           # Пустое поле
                'Team Size': '',         # Пустое поле
                'Location': '',          # Пустое поле
                'Jobs': '',              # Пустое поле
                'Company Link': '',      # Пустое поле
                'Linkedin Link': company.get('linkedin_url', ''),
                'Followers_Count': '',   # Пустое поле
                'Has_YC_Batch_Indicator': True,  # Всегда True для YC S25
                'Long Description': '',  # Пустое поле
                'YC Page': ''           # Пустое поле
            })
        
        new_df = pd.DataFrame(new_data)
        
        # Объединить и сохранить
        if not df.empty:
            combined_df = pd.concat([df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        # Сохранить в CSV
        combined_df.to_csv('data.csv', index=False)
        
        print(f"✅ Successfully added {len(new_companies)} new companies to data.csv")
        print(f"📊 Total companies in database: {len(combined_df)}")
        
        # Показать добавленные компании
        if new_companies:
            print("\n🏢 Added companies:")
            for i, company in enumerate(new_companies):
                linkedin_status = "✅" if company.get('linkedin_url') else "❌"
                print(f"   {i+1}. {company['title']} {linkedin_status}")
        
        return len(new_companies)
        combined_df.to_csv('data.csv', index=False)
        new_df.to_csv('linkedin_multipage_results.csv', index=False)
        
        print(f"✅ Added {len(new_df)} new YC S25 companies to data.csv")
        print(f"📊 Total companies in data.csv: {len(combined_df)}")
        
        # Показать добавленные компании
        print(f"\n📋 Added companies:")
        for _, row in new_df.iterrows():
            linkedin_url = row['Linkedin Link'] if row['Linkedin Link'] else 'No URL'
            print(f"   🏢 {row['Title']} - {linkedin_url}")

def main():
    scraper = LinkedInMultiPageSearch()
    
    print("🚀 LinkedIn YC S25 Multi-Page Search")
    print("=" * 60)
    print("📋 This script will:")
    print("   1. Open LinkedIn in a browser window")
    print("   2. Wait for you to log in manually")
    print("   3. Search through all 10 pages of YC S25 results")
    print("   4. Extract companies with (YC S25) pattern from each page")
    print("   5. Save all unique companies to data.csv")
    print("   6. Will find all available YC S25 companies across pages")
    print("=" * 60)
    
    companies = scraper.search_all_pages()
    
    if companies:
        scraper.save_results(companies)
        print(f"\n🎉 SUCCESS! Found {len(companies)} unique YC S25 companies across 10 pages!")
    else:
        print("❌ No YC S25 companies found")

if __name__ == "__main__":
    main()