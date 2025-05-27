# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multilingual Duolingo vocabulary scraper that extracts words and their English translations from duome.eu, generates audio pronunciations using Google Text-to-Speech, and creates Anki flashcard decks (.apkg files). Supports multiple languages with Russian as the default.

## Core Architecture

**Single-file application:** `scraper.py` contains all functionality:
- Web scraping using requests and BeautifulSoup to parse duome.eu vocabulary pages
- Audio generation using gTTS (Google Text-to-Speech) with rate limiting and error handling
- Anki deck creation using genanki library with dual card templates (Target Language→English and English→Target Language)
- File management for audio assets

**Data flow:**
1. Scrapes vocabulary from https://duome.eu/vocabulary/en/{lang_code}/skills
2. Parses HTML to extract target language words, pronunciations, and English translations
3. Generates MP3 audio files for each word (stored in `audio_{lang_code}/` directory)
4. Creates Anki package with flashcards and embedded audio

## Dependencies

The script requires these Python packages:
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `genanki` - Anki deck generation
- `gtts` - Google Text-to-Speech
- Standard library: `os`, `re`, `random`, `sys`, `argparse`

**Installation:** See `setup.md` for detailed environment setup instructions and `requirements.txt` for exact package versions.

## Running the Application

```bash
# Default (Russian)
python scraper.py

# Specify different language
python scraper.py -l es  # Spanish
python scraper.py -l fr  # French
python scraper.py -l de  # German

# Show help
python scraper.py --help
```

**Command Line Options:**
- `-l, --language`: Target language code (ISO 639-1). Default: `ru` (Russian)
  - Supported: ru, es, fr, de, it, pt, nl, pl, tr, ja, ko, zh, ar, hi

**Output:**
- `duolingo_{lang_code}_vocabulary.apkg` - Anki deck file
- `audio_{lang_code}/*.mp3` - Audio pronunciation files for target language

## Error Handling

The scraper includes specific handling for:
- HTTP 429 (rate limiting) from Google TTS - stops audio generation and continues without audio
- Network errors during web scraping
- Missing vocabulary entries (indicates website structure changes)

## Audio Generation

Audio files are generated only if they don't already exist, allowing for incremental runs. The script handles TTS rate limiting gracefully by skipping remaining audio generation while still creating the Anki deck.

## HTML Parsing Logic

The scraper looks for `<span class="wA">` elements with `title` attributes containing pronunciation and translation data in the format: `[pronunciation] translation`.