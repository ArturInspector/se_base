import os

PRICING_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../clean_pricing_data.json')

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 400
DEFAULT_TIMEOUT = 15

MAX_DIALOGUE_CONTEXT_SIZE = 2000
DIALOGUE_CONTEXT_LIMIT = 10

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

