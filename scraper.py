import requests
from bs4 import BeautifulSoup
import json
import time
import string

def scrape_fighters():
    base_url = 'http://www.ufcstats.com/statistics/fighters?char={char}&page=all'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    fighters = []
    
    for char in string.ascii_lowercase:
        url = base_url.format(char=char)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraping lightweight fighters for initial {char.upper()} from {url}")
        
        for attempt in range(5):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', class_='b-statistics__table')
                if not table:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: Table with class 'b-statistics__table' not found for initial {char.upper()}")
                    break
                
                rows = table.find_all('tr')[1:]
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
                        weight_class = cols[4].text.strip()
                        if '155 lbs.' not in weight_class:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Skipping {name}: Not lightweight ({weight_class})")
                            continue
                        wins = cols[7].text.strip()
                        losses = cols[8].text.strip()
                        draws = cols[9].text.strip()
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
                        time.sleep(2)
                    except Exception as e:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error processing row {i} for initial {char.upper()}: {e}")
                        continue
                break
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Attempt {attempt + 1} failed for initial {char.upper()}: {e}")
                time.sleep(5)
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] All attempts failed for initial {char.upper()}")
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraped {len(fighters)} lightweight fighters")
    return fighters

def scrape_fighter_details(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    for attempt in range(5):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            name_elem = soup.find('span', class_='b-content__title-highlight')
            if not name_elem:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: Name not found for {url}")
                return None
            name = name_elem.text.strip()
            
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
            
            stats = soup.find_all('li', class_='b-list__box-list-item')
            fighter_data = {
                'name': name,
                'weight_class': weight_class,
                'slpm': 0.0,
                'sapm': 0.0,
                'str_acc': 0.0,
                'str_def': 0.0,
                'td_avg': 0.0,
                'td_acc': 0.0,
                'td_def': 0.0,
                'sub_avg': 0.0
            }
            
            for stat in stats:
                text = stat.text.strip()
                try:
                    if 'SLpM' in text:
                        fighter_data['slpm'] = float(text.split(':')[-1].strip()) if text.split(':')[-1].strip() and text.split(':')[-1].strip() != '--' else 0.0
                    elif 'SApM' in text:
                        fighter_data['sapm'] = float(text.split(':')[-1].strip()) if text.split(':')[-1].strip() and text.split(':')[-1].strip() != '--' else 0.0
                    elif 'Str. Acc' in text:
                        fighter_data['str_acc'] = float(text.split(':')[-1].strip().replace('%', '')) / 100 if text.split(':')[-1].strip().replace('%', '') and text.split(':')[-1].strip().replace('%', '') != '--' else 0.0
                    elif 'Str. Def' in text:
                        fighter_data['str_def'] = float(text.split(':')[-1].strip().replace('%', '')) / 100 if text.split(':')[-1].strip().replace('%', '') and text.split(':')[-1].strip().replace('%', '') != '--' else 0.0
                    elif 'TD Avg' in text:
                        fighter_data['td_avg'] = float(text.split(':')[-1].strip()) if text.split(':')[-1].strip() and text.split(':')[-1].strip() != '--' else 0.0
                    elif 'TD Acc' in text:
                        fighter_data['td_acc'] = float(text.split(':')[-1].strip().replace('%', '')) / 100 if text.split(':')[-1].strip().replace('%', '') and text.split(':')[-1].strip().replace('%', '') != '--' else 0.0
                    elif 'TD Def' in text:
                        fighter_data['td_def'] = float(text.split(':')[-1].strip().replace('%', '')) / 100 if text.split(':')[-1].strip().replace('%', '') and text.split(':')[-1].strip().replace('%', '') != '--' else 0.0
                    elif 'Sub. Avg' in text:
                        fighter_data['sub_avg'] = float(text.split(':')[-1].strip()) if text.split(':')[-1].strip() and text.split(':')[-1].strip() != '--' else 0.0
                except Exception as e:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error parsing stat for {name}: {text}, {e}")
            
            if any(fighter_data[metric] == 0 for metric in ['slpm', 'sapm', 'str_acc', 'str_def', 'td_avg', 'td_acc', 'td_def']):
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Skipping {name}: Invalid stats (SLpM={fighter_data['slpm']}, SApM={fighter_data['sapm']}, Str.Acc={fighter_data['str_acc']})")
                return None
                
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