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
python scraper.py -l ru
```

## Dependencies

- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing  
- `genanki` - Anki deck generation
- `gtts` - Google Text-to-Speech

## Troubleshooting

- If you get SSL errors with `gtts`, try upgrading pip: `pip install --upgrade pip`
- If `genanki` fails to install, make sure you have a recent version of Python (3.7+)
- For audio generation issues, ensure you have an internet connection for Google TTS