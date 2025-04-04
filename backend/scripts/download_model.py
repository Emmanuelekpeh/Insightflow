import os
import time
import sys
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

def download_model():
    print('INFO: Cache directory:', os.getenv('TRANSFORMERS_CACHE'))
    print('INFO: Downloading sentiment analysis model...')

    model_id = "distilbert-base-uncased-finetuned-sst-2-english"
    cache_dir = os.getenv('TRANSFORMERS_CACHE', '/tmp/transformers_cache')

    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # First try to download and cache the tokenizer
            print(f'INFO: Downloading tokenizer (attempt {attempt + 1}/{max_retries})...')
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=cache_dir,
                local_files_only=False
            )

            # Then download and cache the model
            print(f'INFO: Downloading model (attempt {attempt + 1}/{max_retries})...')
            model = AutoModelForSequenceClassification.from_pretrained(
                model_id,
                cache_dir=cache_dir,
                local_files_only=False
            )

            # Finally, create and test the pipeline
            print('INFO: Creating pipeline...')
            sentiment_pipeline = pipeline(
                'sentiment-analysis',
                model=model,
                tokenizer=tokenizer,
                device=-1  # Use CPU
            )

            # Test the pipeline
            print('INFO: Testing model with sample text...')
            result = sentiment_pipeline('This is a test sentence.')
            print(f'INFO: Model test result: {result}')
            print('INFO: Model download and test successful!')
            return True

        except Exception as e:
            print(f'WARNING: Attempt {attempt + 1} failed: {str(e)}', file=sys.stderr)
            if attempt < max_retries - 1:
                print(f'INFO: Retrying in {retry_delay} seconds...')
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print('ERROR: All attempts failed. Could not download and initialize model.', file=sys.stderr)
                raise

if __name__ == '__main__':
    try:
        download_model()
    except Exception as e:
        print(f'ERROR: Model download/test failed: {e}', file=sys.stderr)
        sys.exit(1) 