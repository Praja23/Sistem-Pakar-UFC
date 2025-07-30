import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def predict_winner(fighter_a, fighter_b):
    # Weights for metrics (SApM negative because lower is better)
    weights = {
        'slpm': 0.20,
        'sapm': -0.15,
        'str_acc': 0.20,
        'str_def': 0.15,
        'td_avg': 0.15,
        'td_acc': 0.10,
        'td_def': 0.10,
        'sub_avg': 0.05
    }
    
    # Normalize stats
    max_values = {
        'slpm': 10.0,
        'sapm': 10.0,
        'str_acc': 1.0,
        'str_def': 1.0,
        'td_avg': 10.0,
        'td_acc': 1.0,
        'td_def': 1.0,
        'sub_avg': 5.0
    }
    
    # User-friendly metric names
    metric_names = {
        'slpm': 'Pukulan Mendarat per Menit (pukulan/menit)',
        'sapm': 'Pukulan Diterima per Menit (pukulan/menit)',
        'str_acc': 'Akurasi Pukulan (%)',
        'str_def': 'Pertahanan Pukulan (%)',
        'td_avg': 'Rata-rata Takedown (takedown/15 menit)',
        'td_acc': 'Akurasi Takedown (%)',
        'td_def': 'Pertahanan Takedown (%)',
        'sub_avg': 'Rata-rata Upaya Submission (submission/15 menit)'
    }
    
    # Calculate scores and collect reasons
    score_a = 0
    score_b = 0
    reasons = []
    
    logging.info(f"Calculating scores for {fighter_a['name']} vs {fighter_b['name']}")
    for metric, weight in weights.items():
        value_a = float(fighter_a.get(metric, 0)) / max_values[metric]
        value_b = float(fighter_b.get(metric, 0)) / max_values[metric]
        score_a += value_a * weight
        score_b += value_b * weight
        logging.info(f"Metric {metric}: {fighter_a['name']}={value_a:.3f}, {fighter_b['name']}={value_b:.3f}, Weight={weight}")
        
        metric_name = metric_names[metric]
        display_a = fighter_a.get(metric, 0)
        display_b = fighter_b.get(metric, 0)
        if metric in ['str_acc', 'str_def', 'td_acc', 'td_def']:
            display_a = f"{display_a * 100:.0f}%"
            display_b = f"{display_b * 100:.0f}%"
        else:
            display_a = f"{display_a:.2f}"
            display_b = f"{display_b:.2f}"
        
        # Handle SApM (lower is better) and other metrics
        if (value_a > value_b and weight > 0) or (value_a < value_b and weight < 0):
            reasons.append(f"{fighter_a['name']} unggul di {metric_name} ({display_a} vs {display_b})")
        elif (value_b > value_a and weight > 0) or (value_b < value_a and weight < 0):
            reasons.append(f"{fighter_b['name']} unggul di {metric_name} ({display_b} vs {display_a})")
    
    # Determine winner
    winner = fighter_a['name'] if score_a > score_b else fighter_b['name']
    reason_text = ". ".join(reasons) + "." if reasons else "Skor imbang, tapi menang tipis."
    score_a = round(score_a * 100, 2)
    score_b = round(score_b * 100, 2)
    
    logging.info(f"Final scores: {fighter_a['name']}={score_a}, {fighter_b['name']}={score_b}, Winner={winner}")
    
    return winner, score_a, score_b, reason_text