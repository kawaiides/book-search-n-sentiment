import re
import requests
from collections import defaultdict
import os
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 
# --------------------------
# Configuration
# --------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")
# --------------------------
# Text Processing Utilities
# --------------------------

def clean_text(text):
    """Normalize text for analysis"""
    return re.sub(r'[^\w\s-]', '', text.lower()).strip()

def tokenize_words(text):
    """Split text into words handling contractions"""
    return re.findall(r"\b[\w'-]+\b", text)

# ---------------------
# Core Analysis Modules
# ---------------------

def count_words(text):
    """Accurate word count implementation"""
    return len(tokenize_words(text))

def analyze_emotion(text):
    """Emotion detection through contextual keyword analysis"""
    emotion_keywords = {
        'joy': {'joy', 'happy', 'hope', 'love', 'peace', 'success'},
        'sadness': {'sad', 'loss', 'pain', 'tears', 'grief', 'death'},
        'anger': {'anger', 'hate', 'rage', 'mad', 'fury', 'resent'},
        'fear': {'fear', 'terror', 'scared', 'anxiety', 'dread'},
        'neutral': {'the', 'and', 'but', 'then'}
    }
    
    words = tokenize_words(clean_text(text))
    emotion_scores = defaultdict(int)
    
    for word in words:
        for emotion, terms in emotion_keywords.items():
            if word in terms:
                # Check context within 3-word window
                idx = words.index(word)
                context = words[max(0,idx-2):min(len(words),idx+3)]
                positive_modifiers = {'very', 'extremely', 'truly'}
                emotion_scores[emotion] += 1 + sum(1 for w in context if w in positive_modifiers)
                
    return max(emotion_scores, key=emotion_scores.get, default='neutral')

# --------------------------
# Book Matching System
# --------------------------

BOOK_DATABASE = {
    "Man’s Search for Meaning": {
        "keywords": {'concentration camp', 'logotherapy', 'suffering', 'meaning', 'auschwitz', 'frankl'},
        "themes": ["Holocaust survival", "Existential purpose", "Psychological resilience"]
    },
    "To Kill a Mockingbird": {
        "keywords": {'mockingbird', 'atticus finch', 'racial injustice', 'maycomb', 'boo radley', 'scout'},
        "themes": ["Racial inequality", "Moral growth", "Childhood innocence"]
    },
    "The Alchemist": {
        "keywords": {'personal legend', 'soul of the world', 'alchemist', 'omens', 'pyramids', 'santiago'},
        "themes": ["Self-discovery", "Spiritual journey", "Destiny"]
    },
    "1984": {
        "keywords": {'big brother', 'thought police', 'newspeak', 'dystopia', 'doublethink'},
        "themes": ["Totalitarianism", "Surveillance", "Reality control"]
    }
}

def local_book_match(text):
    """Local book matching using keyword frequency"""
    clean = clean_text(text)
    matches = defaultdict(int)
    
    for book, data in BOOK_DATABASE.items():
        for keyword in data['keywords']:
            if re.search(rf'\b{re.escape(keyword)}\b', clean):
                matches[book] += 3  # Higher weight for exact matches
            elif keyword in clean:
                matches[book] += 1
                
    return sorted(matches, key=matches.get, reverse=True)[:3]

# ---------------------
# Gemini API Integration
# ---------------------

def gemini_query(prompt):
    """Generic Gemini API query handler"""
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}",
            json=payload,
            timeout=15
        )
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"API Error: {e}")
        return None

def gemini_book_search(text):
    """Enhanced book identification with contextual analysis"""
    book_list = ", ".join(BOOK_DATABASE.keys())
    prompt = f"""Identify which book the passage most likely comes from:.
    Consider themes, writing style, and characteristic elements. ONLY OUTPUT THE BOOK NAME. Passage: {text[:1500]}..."""
    
    result = gemini_query(prompt)
    return [result.strip()] if result else []

def gemini_summarize(text):
    """Generate contextual summary using Gemini"""
    prompt = f"Provide a concise 2-3 sentence summary focusing on key themes and narrative elements: {text[:3000]}"
    return gemini_query(prompt) or "Summary unavailable"

# ---------------------
# Main Analysis Flow
# ---------------------

def analyze_literature(text):
    """Complete passage analysis workflow"""
    return {
        'word_count': count_words(text),
        'emotion': analyze_emotion(text),
        'local_books': local_book_match(text),
        'api_books': gemini_book_search(text),
        'summary': gemini_summarize(text)
    }

def display_results(analysis):
    """Formatted output presentation"""
    print(f"1. Total Words: {analysis['word_count']}")
    print(f"2. Predominant Emotion: {analysis['emotion'].title()}")
    print("3. Possible Source Books:")
    print(f"   - Local Matches: {', '.join(analysis['local_books'])}")
    if analysis['api_books']:
        print(f"   - AI Suggestions: {', '.join(analysis['api_books'])}")
    print(f"4. Summary:\n{analysis['summary']}")

# ---------------------
# Execution Example
# ---------------------

if __name__ == "__main__":
    # Example usage with hardcoded text
    sample_passage = input("Enter your passage: ")
    analysis = analyze_literature(sample_passage)
    display_results(analysis)