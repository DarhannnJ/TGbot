from datetime import datetime, timedelta
from dateutil.parser import parse

def is_within_last_month(date_str):
    try:
        transaction_date = parse(date_str)
        return (datetime.now() - transaction_date) <= timedelta(days=30)
    except:
        return False

def calculate_reliability(transactions):
    if not transactions:
        return 0
    
    total_score = 0
    for t in transactions:
        score = 0
        if "дархан" in t["recipient"].lower():
            score += 40
        if t["amount"] > 0:
            score += 30
        if is_within_last_month(t["date"]):
            score += 30
        total_score += score
    
    return min(100, total_score // len(transactions))