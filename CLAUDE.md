# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multilingual Duolingo vocabulary scraper that extracts words and their English translations from duome.eu, generates contextual example sentences using Claude API, creates audio pronunciations for both words and sentences using Google Text-to-Speech, and builds enhanced Anki flashcard decks (.apkg files). Supports multiple languages with Russian as the default.

## Core Architecture

**Single-file application:** `scraper.py` contains all functionality:
- Web scraping using requests and BeautifulSoup to parse duome.eu vocabulary pages
- Claude API integration for translating words missing English translations
- Claude API sentence generation for contextual example sentences with grammatically correct structure
- Audio generation using gTTS (Google Text-to-Speech) for both words and sentences with rate limiting and error handling
- Anki deck creation using genanki library with enhanced dual card templates including example sentences and audio
- File management for word and sentence audio assets
- APKG file reading to reuse existing translations and sentences for incremental updates

**Data flow:**
1. Loads existing translations and sentence examples from previous APKG files (if they exist)
2. Scrapes vocabulary from https://duome.eu/vocabulary/en/{lang_code}/skills
3. Parses HTML to extract target language words, pronunciations, and English translations
4. Uses Claude API to translate words missing English translations (if API key provided)
5. Generates contextual example sentences using Claude API for words with translations
6. Creates MP3 audio files for words (stored in `audio_{lang_code}/` directory)
7. Creates MP3 audio files for sentences (stored in `audio_{lang_code}_sentences/` directory)
8. Builds enhanced Anki package with flashcards containing words, sentences, and embedded audio

## Dependencies

The script requires these Python packages:
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `genanki` - Anki deck generation
- `gtts` - Google Text-to-Speech
- `anthropic` - Claude API client (optional, for translations and example sentence generation)
- Standard library: `os`, `re`, `random`, `sys`, `argparse`, `zipfile`, `sqlite3`, `shutil`, `tempfile`

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

# With Claude API for translations and example sentences
python scraper.py -l ja --api-key your_anthropic_api_key
```

**Command Line Options:**
- `-l, --language`: Target language code (ISO 639-1). Default: `ru` (Russian)
  - Supported: ru, es, fr, de, it, pt, nl, pl, tr, ja, ko, zh, ar, hi
- `--api-key`: Anthropic API key for translating missing words and generating example sentences (optional)

**Output:**
- `duolingo_{lang_code}_vocabulary.apkg` - Enhanced Anki deck file with example sentences
- `audio_{lang_code}/*.mp3` - Audio pronunciation files for target language words
- `audio_{lang_code}_sentences/*.mp3` - Audio files for example sentences

## Error Handling

The scraper includes specific handling for:
- HTTP 429 (rate limiting) from Google TTS - stops audio generation and continues without audio
- Network errors during web scraping
- Missing vocabulary entries (indicates website structure changes)
- Claude API errors during sentence generation - continues with word-only cards
- APKG file reading errors - starts fresh if existing file is corrupted

## Audio Generation

Audio files for both words and sentences are generated only if they don't already exist, allowing for incremental runs. The script handles TTS rate limiting gracefully by skipping remaining audio generation while still creating the Anki deck. Sentence audio files are stored in a separate directory with `_sentence.mp3` suffix.

## Enhanced APKG Format

The scraper now creates enhanced Anki cards with 7 fields:
1. **Target** - Target language word
2. **Pronunciation** - Phonetic pronunciation guide
3. **English** - English translation
4. **Audio** - Word audio file reference
5. **ExampleSentence** - Contextual sentence in target language
6. **SentenceAudio** - Sentence audio file reference
7. **SentenceTranslation** - English translation of example sentence

**Card Templates:**
- **Target → English**: Shows word + example sentence with audio on front, translations on back
- **English → Target**: Shows English word + sentence translation on front, target content on back

**Backward Compatibility:**
The scraper can read both old (4-field) and new (7-field) APKG formats, preserving existing data while adding enhancements.

## HTML Parsing Logic

The scraper looks for `<span class="wA">` elements with `title` attributes containing pronunciation and translation data in the format: `[pronunciation] translation`.