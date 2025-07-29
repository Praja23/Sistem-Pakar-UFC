import requests
from bs4 import BeautifulSoup
import json
import time
import string

def scrape_fighters():
    base_url = 'http://www.ufcstats.com/statistics/fighters?char={char}&page=all'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    fighters = []
    
    # Loop through all initials (A-Z)
    for char in string.ascii_lowercase:
        url = base_url.format(char=char)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraping lightweight fighters for initial {char.upper()} from {url}")
        
        for attempt in range(5):  # Retry up to 5 times
            try:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', class_='b-statistics__table')
                if not table:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: Table with class 'b-statistics__table' not found for initial {char.upper()}")
                    break
                
                rows = table.find_all('tr')[1:]  # Skip header
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Found {len(rows)} rows for initial {char.upper()}")
                for i, row in enumerate(rows):
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 10:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Skipping row {i} for initial {char.upper()}: Not enough columns")
                            continue
                        first_name = cols[0].text.strip()
                        last_name = cols[1].text.strip()
                        name = f"{first_name} {last_name}".strip()
                        weight_class = cols[4].text.strip()  # Weight class in 5th column
                        if '155 lbs.' not in weight_class:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Skipping {name}: Not lightweight ({weight_class})")
                            continue
                        wins = cols[7].text.strip()  # Wins in 8th column
                        losses = cols[8].text.strip()  # Losses in 9th column
                        draws = cols[9].text.strip()  # Draws in 10th column
                        fighter_url = cols[0].find('a')
                        if not fighter_url:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Skipping {name}: No fighter URL found")
                            continue
                        fighter_url = fighter_url['href']
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraping lightweight fighter {name} from {fighter_url}")
                        fighter_data = scrape_fighter_details(fighter_url)
                        if fighter_data and fighter_data['weight_class'] == 'Lightweight':
                            fighter_data['wins'] = int(wins) if wins.isdigit() else 0
                            fighter_data['losses'] = int(losses) if losses.isdigit() else 0
                            fighter_data['draws'] = int(draws) if draws.isdigit() else 0
                            fighters.append(fighter_data)
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Added lightweight fighter: {name} ({wins}-{losses}-{draws})")
                        time.sleep(2)  # Delay for lightweight fighters
                    except Exception as e:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error processing row {i} for initial {char.upper()}: {e}")
                        continue
                break  # Exit retry loop if successful
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempt {attempt + 1} failed for initial {char.upper()}: {e}")
                time.sleep(5)
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] All attempts failed for initial {char.upper()}")
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraped {len(fighters)} lightweight fighters")
    return fighters

def scrape_fighter_details(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for attempt in range(5):  # Retry up to 5 times
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get name
            name_elem = soup.find('span', class_='b-content__title-highlight')
            if not name_elem:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: Name not found for {url}")
                return None
            name = name_elem.text.strip()
            
            # Get weight class
            weight_class = 'Other'
            details_section = soup.find('div', class_='b-list__info-box')
            if details_section:
                labels = details_section.find_all('li', class_='b-list__box-list-item')
                for label in labels:
                    text = label.text.strip()
                    if 'Weight' in text and '155 lbs' in text:
                        weight_class = 'Lightweight'
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Confirmed lightweight for {name}: {text}")
                        break
                    else:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Weight class for {name}: {text}")
            
            # Get stats
            stats = soup.find_all('li', class_='b-list__box-list-item')
            fighter_data = {
                'name': name,
                'weight_class': weight_class,
                'slpm': 0.0,
                'str_acc': 0.0,
                'str_def': 0.0,
                'td_avg': 0.0,
                'td_def': 0.0
            }
            
            for stat in stats:
                text = stat.text.strip()
                try:
                    if 'SLpM' in text:
                        fighter_data['slpm'] = float(text.split(':')[-1].strip())
                    elif 'Str. Acc' in text:
                        fighter_data['str_acc'] = float(text.split(':')[-1].strip().replace('%', '')) / 100
                    elif 'Str. Def' in text:
                        fighter_data['str_def'] = float(text.split(':')[-1].strip().replace('%', '')) / 100
                    elif 'TD Avg' in text:
                        fighter_data['td_avg'] = float(text.split(':')[-1].strip())
                    elif 'TD Def' in text:
                        fighter_data['td_def'] = float(text.split(':')[-1].strip().replace('%', '')) / 100
                except Exception as e:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error parsing stat for {name}: {text}, {e}")
            
            return fighter_data
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(5)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] All attempts failed for {url}")
    return None

if __name__ == '__main__':
    fighters = scrape_fighters()
    if fighters:
        with open('fighters_data.json', 'w') as f:
            json.dump(fighters, f, indent=4)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Saved {len(fighters)} lightweight fighters to fighters_data.json")
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] No lightweight fighters scraped")