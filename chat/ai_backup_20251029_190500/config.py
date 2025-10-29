import os

PRICING_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../clean_pricing_data.json')

DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 600
DEFAULT_TIMEOUT = 20

MAX_DIALOGUE_CONTEXT_SIZE = 8000
DIALOGUE_CONTEXT_LIMIT = 20

HOUR_PATTERNS = [
    r'(\d+)\s*час',
    r'(\d+)\s*ч',
    r'на\s*(\d+)\s*час',
    r'(\d+)\s*часов'
]

PEOPLE_PATTERNS = [
    r'(\d+)\s*человек',
    r'(\d+)\s*чел',
    r'(\d+)\s*чел\.',
    r'(\d+)\s*человека'
]

CITY_URL_PATTERN = r'https://www\.avito\.ru/([^/]+)/'

