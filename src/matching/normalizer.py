import re
from typing import Dict
from datetime import datetime

class TextNormalizer:
    def __init__(self):
        self.name_replacements = {
            'trump': ['donald trump', 'djt', 'd. trump', 'donald j. trump', 'donald j trump'],
            'biden': ['joe biden', 'joseph biden', 'j. biden'],
            'harris': ['kamala harris', 'k. harris', 'kamala d. harris'],
            'desantis': ['ron desantis', 'ronald desantis', 'r. desantis'],
            'us': ['united states', 'usa', 'u.s.', 'u.s.a.'],
            'uk': ['united kingdom', 'u.k.', 'great britain', 'britain'],
            'fed': ['federal reserve', 'federal reserve bank'],
            'gdp': ['gross domestic product'],
        }

        self.reverse_map = {}
        for standard, variants in self.name_replacements.items():
            for variant in variants:
                self.reverse_map[variant.lower()] = standard

        self.stopwords = {
            'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with',
            'will', 'be', 'is', 'are', 'was', 'were', 'been', 'being'
        }

    def normalize(self, text: str) -> str:
        text = text.lower().strip()

        text = re.sub(r'[^\w\s-]', ' ', text)

        for variant, standard in self.reverse_map.items():
            pattern = r'\b' + re.escape(variant) + r'\b'
            text = re.sub(pattern, standard, text)

        words = text.split()
        words = [w for w in words if w not in self.stopwords or len(w) > 3]

        text = ' '.join(words)

        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def extract_date_context(self, text: str) -> Dict[str, any]:
        text_lower = text.lower()

        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, text_lower)

        month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b'
        months = re.findall(month_pattern, text_lower)

        quarter_pattern = r'\b(q[1-4]|first quarter|second quarter|third quarter|fourth quarter)\b'
        quarters = re.findall(quarter_pattern, text_lower)

        return {
            'years': years,
            'months': months,
            'quarters': quarters,
            'has_date': len(years) > 0 or len(months) > 0
        }

normalizer = TextNormalizer()
