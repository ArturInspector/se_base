import os
from dotenv import load_dotenv

load_dotenv()


class Production:
    PROJECT_NAME = 'SE Members'
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    BOT_TOKEN = os.getenv('BOT_TOKEN')
    BOT_TOKEN_TEST = os.getenv('BOT_TOKEN_TEST')
    BOT_PASSWORD = os.getenv('BOT_PASSWORD', 'password')

    REPORT_BOT_TOKEN = os.getenv('REPORT_BOT_TOKEN')
    REPORT_BOT_PASSWORD = os.getenv('REPORT_BOT_PASSWORD', 'password')

    DADATA_API_KEY = os.getenv('DADATA_API_KEY')
    DADATA_SECRET = os.getenv('DADATA_SECRET')

    AVITO_ID = int(os.getenv('AVITO_ID', 0))
    AVITO_CLIENT_ID = os.getenv('AVITO_CLIENT_ID')
    AVITO_SECRET = os.getenv('AVITO_SECRET')
    AVITO_CALLBACK_URL = os.getenv('AVITO_CALLBACK_URL', 'https://se-bot.ru/kek/avito/')
    AVITO_BASE_URL = os.getenv('AVITO_BASE_URL', 'https://api.avito.ru')

    OLD_AVITO_ID = int(os.getenv('OLD_AVITO_ID', 0))
    OLD_AVITO_CLIENT_ID = os.getenv('OLD_AVITO_CLIENT_ID')
    OLD_AVITO_SECRET = os.getenv('OLD_AVITO_SECRET')
    OLD_AVITO_CALLBACK_URL = os.getenv('OLD_AVITO_CALLBACK_URL', 'https://se-bot.ru/kek/avito_old/')
    OLD_AVITO_BASE_URL = os.getenv('OLD_AVITO_BASE_URL', 'https://api.avito.ru')

    GRUZ_AVITO_ID = int(os.getenv('GRUZ_AVITO_ID', 0))
    GRUZ_AVITO_CLIENT_ID = os.getenv('GRUZ_AVITO_CLIENT_ID')
    GRUZ_AVITO_SECRET = os.getenv('GRUZ_AVITO_SECRET')
    GRUZ_AVITO_CALLBACK_URL = os.getenv('GRUZ_AVITO_CALLBACK_URL', 'https://se-bot.ru/kek/avito_old/')
    GRUZ_AVITO_BASE_URL = os.getenv('GRUZ_AVITO_BASE_URL', 'https://api.avito.ru')

    NEW_AVITO_ID = int(os.getenv('NEW_AVITO_ID', 0))
    NEW_AVITO_CLIENT_ID = os.getenv('NEW_AVITO_CLIENT_ID')
    NEW_AVITO_SECRET = os.getenv('NEW_AVITO_SECRET')
    NEW_AVITO_CALLBACK_URL = os.getenv('NEW_AVITO_CALLBACK_URL', 'https://se-bot.ru/kek/avito_new/')
    NEW_AVITO_BASE_URL = os.getenv('NEW_AVITO_BASE_URL', 'https://api.avito.ru')

    WHATSAPP_BASE_URL = os.getenv('WHATSAPP_BASE_URL')
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')

    bitrix_webhook = os.getenv('BITRIX_WEBHOOK')
    chatbot_bitrix_webhook = os.getenv('CHATBOT_BITRIX_WEBHOOK')
    BEELINE_URL = os.getenv('BEELINE_URL', 'https://cloudpbx.beeline.ru/apis/portal/')

    NOTIFICATIONS_BOT_TOKEN = os.getenv('NOTIFICATIONS_BOT_TOKEN')

    BITRIX_WEBHOOK = os.getenv('BITRIX_WEBHOOK')

    BEELINE_TOKEN = os.getenv('BEELINE_TOKEN')

    WHAPI_BASE_URL = os.getenv('WHAPI_BASE_URL', 'https://gate.whapi.cloud')
    WHAPI_TOKEN = os.getenv('WHAPI_TOKEN')
    WHAPI_BUSINESS_TOKEN = os.getenv('WHAPI_BUSINESS_TOKEN')

    KAZAN_ITEM_ID = int(os.getenv('KAZAN_ITEM_ID', 0))

    REDIS_ADDRESS = os.getenv('REDIS_ADDRESS')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

    BITRIX_APP_URL = os.getenv('BITRIX_APP_URL')
    BITRIX_APP_CLIENT_ID = os.getenv('BITRIX_APP_CLIENT_ID')
    BITRIX_APP_CLIENT_SECRET = os.getenv('BITRIX_APP_CLIENT_SECRET')

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    AI_ENABLED = os.getenv('AI_ENABLED', 'True').lower() == 'true'
    AI_FALLBACK_ENABLED = os.getenv('AI_FALLBACK_ENABLED', 'True').lower() == 'true'
    AI_MAX_CONVERSATION_LENGTH = int(os.getenv('AI_MAX_CONVERSATION_LENGTH', 10))
    
    KPI_DASHBOARD_USER = os.getenv('KPI_DASHBOARD_USER', 'admin')
    KPI_DASHBOARD_PASSWORD = os.getenv('KPI_DASHBOARD_PASSWORD', 'change_me_in_production')