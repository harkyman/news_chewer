import re
from itertools import combinations

# A modest set of common articles, conjunctions, and prepositions
STOP_WORDS = {
    "a", "an", "the", 
    "and", "but", "or", "so", "for", "yet", "nor", 
    "in", "on", "at", "to", "from", "by", "with", "about", "as", "of", "into", "over", "under"
}

def clean_text(text: str) -> str:
    """Lowercases, removes special characters, and strips stop words."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    words = text.split()
    filtered_words = [word for word in words if word not in STOP_WORDS]
    
    return " ".join(filtered_words)

def get_ngrams(text: str, n: int) -> set:
    """Generates a set of character n-grams from a string."""
    text = text.replace(" ", "")
    
    if len(text) < n:
        return {text} if text else set()
        
    return set(text[i:i+n] for i in range(len(text) - n + 1))

def calculate_ngram_score(str1: str, str2: str, n: int = 2) -> float:
    """Calculates the Sørensen-Dice coefficient between two strings."""
    cleaned1 = clean_text(str1)
    cleaned2 = clean_text(str2)
    
    grams1 = get_ngrams(cleaned1, n)
    grams2 = get_ngrams(cleaned2, n)
    
    if not grams1 and not grams2:
        return 1.0
    elif not grams1 or not grams2:
        return 0.0
        
    intersection = len(grams1.intersection(grams2))
    return (2.0 * intersection) / (len(grams1) + len(grams2))

def get_best_match(ref_str: str, string_list: list) -> str:
    """
    Compares a reference string against a list of candidate strings.
    Returns the highest scoring candidate if the score is > 0.6, 
    otherwise returns the original reference string.
    """
    best_score = 0.0
    best_match = None
    
    for candidate in string_list:
        score = calculate_ngram_score(ref_str, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate
            
    if best_score > 0.6:
        return best_match
        
    return ref_str

def main():
    phrases = [
        "Russia/Ukraine war",
        "Israel conflict",
        "2026 Iran war and wider Middle East escalation",
        "Climate change",
        "Artificial intelligence safety and regulation",
        "US-China trade tensions and technology competition",
        "The rise of European far-right political movements",
        "Yemen conflict",
        "\"2026 Iran war and wider Middle East escalation\"",
        "\"Russia/Ukraine war\"",
        "Donald Trump Jr.",
        "Hungarian law",
        "War (specifically Ukraine-Russia War)",
        "Arctic geopolitics",
        "EU sanctions",
        "Russia-Ukraine War",
        "International Relations"
    ]
    
    # Store matching pairs
    high_score_pairs = []
    
    # combinations() generates all unique pairs without repeating (e.g., A-B but not B-A)
    for str1, str2 in combinations(phrases, 2):
        score = calculate_ngram_score(str1, str2)
        
        if score > 0.5:
            high_score_pairs.append((score, str1, str2))
            
    # Sort the results from highest score to lowest for easier reading
    high_score_pairs.sort(key=lambda x: x[0], reverse=True)
    
    # Print the output nicely
    print(f"Found {len(high_score_pairs)} pairs with a score > 0.5:\n")
    for score, s1, s2 in high_score_pairs:
        print(f"Score: {score:.3f}")
        print(f"  String 1: {s1}")
        print(f"  String 2: {s2}\n")
        
    return high_score_pairs

if __name__ == "__main__":
    main()