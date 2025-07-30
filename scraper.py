import requests
from bs4 import BeautifulSoup
import json
import time
import string
import logging
from datetime import datetime, timedelta

# Setup logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()  # Output ke terminal
    ]
)

def scrape_fighters():
    base_url = 'http://www.ufcstats.com/statistics/fighters?char={char}&page=all'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    fighters = []
    
    for char in string.ascii_lowercase:
        url = base_url.format(char=char)
        logging.info(f"Scraping lightweight fighters for initial {char.upper()} from {url}")
        
        for attempt in range(5):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', class_='b-statistics__table')
                if not table:
                    logging.error(f"Table with class 'b-statistics__table' not found for initial {char.upper()}")
                    break
                
                rows = table.find_all('tr')[1:]  # Skip header
                logging.info(f"Found {len(rows)} rows for initial {char.upper()}")
                for i, row in enumerate(rows):
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 10:
                            logging.warning(f"Skipping row {i} for initial {char.upper()}: Not enough columns")
                            continue
                        first_name = cols[0].text.strip()
                        last_name = cols[1].text.strip()
                        name = f"{first_name} {last_name}".strip()
                        weight_class = cols[4].text.strip()
                        if '155 lbs.' not in weight_class:
                            logging.info(f"Skipping {name}: Not lightweight ({weight_class})")
                            continue
                        wins = cols[7].text.strip()
                        losses = cols[8].text.strip()
                        draws = cols[9].text.strip()
                        fighter_url = cols[0].find('a')
                        if not fighter_url:
                            logging.warning(f"Skipping {name}: No fighter URL found")
                            continue
                        fighter_url = fighter_url['href']
                        logging.info(f"Scraping lightweight fighter {name} from {fighter_url}")
                        fighter_data = scrape_fighter_details(fighter_url)
                        if fighter_data and fighter_data['weight_class'] == 'Lightweight':
                            fighter_data['wins'] = int(wins) if wins.isdigit() else 0
                            fighter_data['losses'] = int(losses) if losses.isdigit() else 0
                            fighter_data['draws'] = int(draws) if draws.isdigit() else 0
                            # Cek minimal 1 fight
                            if fighter_data['wins'] + fighter_data['losses'] + fighter_data['draws'] == 0:
                                logging.warning(f"Skipping {name}: No fights recorded")
                                continue
                            fighters.append(fighter_data)
                            logging.info(f"Added lightweight fighter: {name} ({wins}-{losses}-{draws})")
                        time.sleep(2)
                    except Exception as e:
                        logging.error(f"Error processing row {i} for initial {char.upper()}: {e}")
                        continue
                break
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed for initial {char.upper()}: {e}")
                time.sleep(5)
        else:
            logging.error(f"All attempts failed for initial {char.upper()}")
    
    # Simpen JSON meski kosong
    with open('fighters_data.json', 'w') as f:
        json.dump(fighters, f, indent=4)
    logging.info(f"Saved {len(fighters)} lightweight fighters to fighters_data.json")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Saved {len(fighters)} lightweight fighters to fighters_data.json")
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
                logging.error(f"Name not found for {url}")
                return None
            name = name_elem.text.strip()
            
            # Cek weight class
            weight_class = 'Other'
            details_section = soup.find('div', class_='b-list__info-box')
            if details_section:
                labels = details_section.find_all('li', class_='b-list__box-list-item')
                for label in labels:
                    text = label.text.strip()
                    if 'Weight' in text and '155 lbs' in text:
                        weight_class = 'Lightweight'
                        logging.info(f"Confirmed lightweight for {name}: {text}")
                        break
            
            # Cek apakah fighter aktif (fight dalam 3 tahun)
            fight_history = soup.find('table', class_='b-fight-details__table')
            is_active = False
            if fight_history:
                fight_rows = fight_history.find_all('tr', class_='b-fight-details__table-row')
                for fight_row in fight_rows[1:]:  # Skip header
                    date_elem = fight_row.find('td', class_='b-fight-details__table-col')
                    if date_elem:
                        fight_date = date_elem.text.strip()
                        for date_format in ['%b. %d, %Y', '%b %d, %Y', '%Y-%m-%d']:
                            try:
                                fight_date_parsed = datetime.strptime(fight_date, date_format)
                                if fight_date_parsed >= datetime.now() - timedelta(days=3*365):
                                    is_active = True
                                    logging.info(f"{name} is active, last fight: {fight_date_parsed.strftime('%Y-%m-%d')}")
                                    break
                            except ValueError:
                                continue
                        if is_active:
                            break
                        logging.warning(f"Invalid date format for {name}: {fight_date}")
                        # Anggap aktif kalo ada fight history
                        is_active = True
                        logging.info(f"Assuming {name} is active due to fight history")
                        break
            
            if not is_active:
                logging.warning(f"Skipping {name}: No active fights in last 3 years")
                return None
            
            # Scrape stats
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
                        value = text.split(':')[-1].strip()
                        fighter_data['slpm'] = float(value) if value and value != '--' else 0.0
                    elif 'SApM' in text:
                        value = text.split(':')[-1].strip()
                        fighter_data['sapm'] = float(value) if value and value != '--' else 0.0
                    elif 'Str. Acc' in text or 'Striking Accuracy' in text:
                        value = text.split(':')[-1].strip().replace('%', '')
                        fighter_data['str_acc'] = float(value) / 100 if value and value != '--' else 0.0
                    elif 'Str. Def' in text or 'Striking Defense' in text:
                        value = text.split(':')[-1].strip().replace('%', '')
                        fighter_data['str_def'] = float(value) / 100 if value and value != '--' else 0.0
                    elif 'TD Avg' in text or 'Takedown Average' in text:
                        value = text.split(':')[-1].strip()
                        fighter_data['td_avg'] = float(value) if value and value != '--' else 0.0
                    elif 'TD Acc' in text or 'Takedown Accuracy' in text:
                        value = text.split(':')[-1].strip().replace('%', '')
                        fighter_data['td_acc'] = float(value) / 100 if value and value != '--' else 0.0
                    elif 'TD Def' in text or 'Takedown Defense' in text:
                        value = text.split(':')[-1].strip().replace('%', '')
                        fighter_data['td_def'] = float(value) / 100 if value and value != '--' else 0.0
                    elif 'Sub. Avg' in text or 'Submission Average' in text:
                        value = text.split(':')[-1].strip()
                        fighter_data['sub_avg'] = float(value) if value and value != '--' else 0.0
                except Exception as e:
                    logging.error(f"Error parsing stat for {name}: {text}, {e}")
            
            # Filter: Simpen kalo ada minimal satu stat utama > 0
            if fighter_data['slpm'] == 0 and fighter_data['sapm'] == 0 and fighter_data['td_avg'] == 0:
                logging.warning(f"Skipping {name}: All main stats are 0 (SLpM={fighter_data['slpm']}, SApM={fighter_data['sapm']}, TD Avg={fighter_data['td_avg']})")
                return None
                
            return fighter_data
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(5)
    logging.error(f"All attempts failed for {url}")
    return None

if __name__ == '__main__':
    fighters = scrape_fighters()
    logging.info(f"Final count: {len(fighters)} lightweight fighters scraped")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Final count: {len(fighters)} lightweight fighters scraped")