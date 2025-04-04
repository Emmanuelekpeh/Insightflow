import os
import time
from transformers import pipeline

def download_model():
    print('INFO: Cache directory:', os.getenv('TRANSFORMERS_CACHE'))
    print('INFO: Downloading sentiment analysis model...')

    for attempt in range(3):
        try:
            model = pipeline(
                'sentiment-analysis',
                model='distilbert-base-uncased-finetuned-sst-2-english',
                device=-1,
                cache_dir='/tmp/transformers_cache'
            )
            print('INFO: Testing model with sample text...')
            result = model('This is a test sentence.')
            print(f'INFO: Model test result: {result}')
            print('INFO: Model download and test successful!')
            return
        except Exception as e:
            print(f'WARNING: Attempt {attempt + 1} failed: {e}')
            if attempt == 2:
                raise
            time.sleep(5)

if __name__ == '__main__':
    download_model() 