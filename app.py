from flask import Flask, render_template, request, jsonify
import json
import os
import time
import schedule
import threading
from expert_system import predict_winner
from scraper import scrape_fighters

app = Flask(__name__)
fighters_dict = {}

def load_fighters():
    global fighters_dict
    json_file = 'fighters_data.json'
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking for existing fighter data...")
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as file:
                fighters = json.load(file)
            lightweight_fighters = [f for f in fighters if f['weight_class'] == 'Lightweight']
            if lightweight_fighters:
                fighters_dict = {f['name'].strip().lower(): f for f in fighters}
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Loaded {len(fighters)} fighters, {len(lightweight_fighters)} lightweight")
                return fighters_dict
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] JSON exists but no lightweight fighters")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error loading JSON: {e}")
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] No valid JSON, please run scraper.py or use Refresh button")
    return {}

@app.route('/')
def index():
    fighters = load_fighters()
    fighter_names = [f['name'] for f in fighters.values() if f['weight_class'] == 'Lightweight']
    last_updated = os.path.getmtime('fighters_data.json') if os.path.exists('fighters_data.json') else time.time()
    last_updated_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_updated))
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sending {len(fighter_names)} lightweight fighters to frontend")
    return render_template('index.html', fighters=fighter_names, last_updated=last_updated_str)

@app.route('/refresh', methods=['POST'])
def refresh():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Manual refresh triggered")
    fighters = scrape_fighters()
    if fighters:
        try:
            with open('fighters_data.json', 'w') as file:
                json.dump(fighters, file, indent=4)
            global fighters_dict
            fighters_dict = {f['name'].strip().lower(): f for f in fighters}
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scraped and saved {len(fighters)} lightweight fighters")
            fighter_names = [f['name'] for f in fighters if f['weight_class'] == 'Lightweight']
            return jsonify({'status': 'success', 'fighters': fighter_names, 'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')})
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error saving JSON: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to save fighter data'}), 500
    return jsonify({'status': 'error', 'message': 'No fighters scraped'}), 500

@app.route('/predict', methods=['POST'])
def predict():
    fighter_a = request.form['fighter_a'].strip()
    fighter_b = request.form['fighter_b'].strip()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Predicting: {fighter_a} vs {fighter_b}")
    fighters = load_fighters()
    
    fighter_a_data = fighters.get(fighter_a.lower())
    fighter_b_data = fighters.get(fighter_b.lower())
    
    if not fighter_a_data or not fighter_b_data:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fighter not found: {fighter_a} or {fighter_b}")
        return jsonify({'error': 'Fighter not found'}), 404
    
    try:
        winner, score_a, score_b, reason = predict_winner(fighter_a_data, fighter_b_data)
        response = {
            'winner': winner,
            'fighter_a': {'name': fighter_a, 'score': score_a},
            'fighter_b': {'name': fighter_b, 'score': score_b},
            'reason': reason
        }
        if all(key in fighter_a_data for key in ['wins', 'losses', 'draws']):
            response['fighter_a']['record'] = f"{fighter_a_data['wins']}-{fighter_a_data['losses']}-{fighter_a_data['draws']}"
        else:
            response['fighter_a']['record'] = "N/A"
        if all(key in fighter_b_data for key in ['wins', 'losses', 'draws']):
            response['fighter_b']['record'] = f"{fighter_b_data['wins']}-{fighter_b_data['losses']}-{fighter_b_data['draws']}"
        else:
            response['fighter_b']['record'] = "N/A"
        return jsonify(response)
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error in predict_winner: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

def job():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scheduled scrape job running...")
    fighters = scrape_fighters()
    if fighters:
        with open('fighters_data.json', 'w') as file:
            json.dump(fighters, file, indent=4)
        global fighters_dict
        fighters_dict = {f['name'].strip().lower(): f for f in fighters}
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Scheduled scrape saved {len(fighters)} lightweight fighters")

schedule.every().day.at("02:00").do(job)

if __name__ == '__main__':
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)
    threading.Thread(target=run_schedule, daemon=True).start()
    app.run(debug=True)