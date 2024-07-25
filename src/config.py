import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY')
    ELASTICSEARCH_HOSTS=os.environ.get('ELASTICSEARCH_HOSTS')
    ELASTICSEARCH_API_KEY_FORMAT=os.environ.get('ELASTICSEARCH_API_KEY_FORMAT')
