# Environment Setup

## Option 1: Using Mamba/Conda

### Create and activate environment:
```bash
# Create new environment
mamba create -n duolingo_scraper python=3.9

# Activate environment
mamba activate duolingo_scraper

# Install dependencies
pip install -r requirements.txt
```

### Run the scraper:
```bash
# With environment activated
python scraper.py -l ru

# With Claude API for enhanced features (recommended)
python scraper.py -l ru --api-key your_anthropic_api_key

# Or run directly without activating
mamba run -n duolingo_scraper python scraper.py -l ru
```

## Option 2: Using pip/venv

### Create and activate virtual environment:
```bash
# Create virtual environment
python -m venv duolingo_scraper_env

# Activate (macOS/Linux)
source duolingo_scraper_env/bin/activate

# Activate (Windows)
duolingo_scraper_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the scraper:
```bash
# Basic usage
python scraper.py -l ru

# With Claude API for enhanced features (recommended)
python scraper.py -l ru --api-key your_anthropic_api_key
```

## Dependencies

- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing  
- `genanki` - Anki deck generation
- `gtts` - Google Text-to-Speech
- `anthropic` - Claude API for translations and example sentences (optional)

## Claude API Setup (Optional but Recommended)

For enhanced features including translations of missing words and contextual example sentences:

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Set up billing (minimum $5 payment required)
3. Use the `--api-key` parameter when running the scraper

**Benefits of using Claude API:**
- Translates words that don't have English translations from duome.eu
- Generates contextual example sentences for better vocabulary learning
- Creates audio for example sentences
- Enhances flashcards with real-world usage examples

## Troubleshooting

- If you get SSL errors with `gtts`, try upgrading pip: `pip install --upgrade pip`
- If `genanki` fails to install, make sure you have a recent version of Python (3.7+)
- For audio generation issues, ensure you have an internet connection for Google TTS
- If Claude API fails, check your API key and billing status at console.anthropic.com
- The scraper will work without Claude API but won't generate example sentences
- If sentence audio seems mismatched, the scraper automatically detects and regenerates corrupted audio files

## Audio File Management

The scraper creates separate directories for different audio types:
- `audio_{language}/` - Word pronunciation files
- `audio_{language}_sentences/` - Example sentence audio files with `.txt` metadata for validation

**Audio Validation**: Each sentence audio file is paired with a `.txt` metadata file containing the exact sentence text. This ensures that if sentences change between runs, the audio is automatically regenerated to match.