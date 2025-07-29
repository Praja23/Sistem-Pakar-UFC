def predict_winner(fighter_a, fighter_b):
    # Weights for metrics
    weights = {
        'slpm': 0.30,
        'str_acc': 0.25,
        'str_def': 0.20,
        'td_avg': 0.15,
        'td_def': 0.10
    }
    
    # Normalize stats
    max_values = {
        'slpm': 10.0,
        'str_acc': 1.0,
        'str_def': 1.0,
        'td_avg': 10.0,
        'td_def': 1.0
    }
    
    # Calculate scores and collect reasons
    score_a = 0
    score_b = 0
    reasons = []
    
    for metric, weight in weights.items():
        value_a = fighter_a.get(metric, 0) / max_values[metric]
        value_b = fighter_b.get(metric, 0) / max_values[metric]
        score_a += value_a * weight
        score_b += value_b * weight
        if value_a > value_b:
            reasons.append(f"{fighter_a['name']} unggul di {metric.upper()} ({fighter_a.get(metric, 0):.2f} vs {fighter_b.get(metric, 0):.2f})")
        elif value_b > value_a:
            reasons.append(f"{fighter_b['name']} unggul di {metric.upper()} ({fighter_b.get(metric, 0):.2f} vs {fighter_a.get(metric, 0):.2f})")
    
    # Determine winner
    winner = fighter_a['name'] if score_a > score_b else fighter_b['name']
    reason_text = ". ".join(reasons) + "." if reasons else "Skor imbang, tapi menang tipis."
    
    return winner, round(score_a * 100, 2), round(score_b * 100, 2), reason_text