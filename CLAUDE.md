# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Duolingo Russian vocabulary scraper that extracts Russian words and their English translations from duome.eu, generates audio pronunciations using Google Text-to-Speech, and creates Anki flashcard decks (.apkg files).

## Core Architecture

**Single-file application:** `scraper.py` contains all functionality:
- Web scraping using requests and BeautifulSoup to parse duome.eu vocabulary pages
- Audio generation using gTTS (Google Text-to-Speech) with rate limiting and error handling
- Anki deck creation using genanki library with dual card templates (Russian→English and English→Russian)
- File management for audio assets

**Data flow:**
1. Scrapes vocabulary from https://duome.eu/vocabulary/en/ru/skills
2. Parses HTML to extract Russian words, pronunciations, and English translations
3. Generates MP3 audio files for each Russian word (stored in `audio/` directory)
4. Creates Anki package with flashcards and embedded audio

## Dependencies

The script requires these Python packages:
- `requests` - HTTP requests for web scraping
- `beautifulsoup4` - HTML parsing
- `genanki` - Anki deck generation
- `gtts` - Google Text-to-Speech
- Standard library: `os`, `re`, `random`, `sys`

## Running the Application

```bash
python scraper.py
```

**Output:**
- `duolingo_russian_vocabulary.apkg` - Anki deck file
- `audio/*.mp3` - Audio pronunciation files for Russian words

## Error Handling

The scraper includes specific handling for:
- HTTP 429 (rate limiting) from Google TTS - stops audio generation and continues without audio
- Network errors during web scraping
- Missing vocabulary entries (indicates website structure changes)

## Audio Generation

Audio files are generated only if they don't already exist, allowing for incremental runs. The script handles TTS rate limiting gracefully by skipping remaining audio generation while still creating the Anki deck.

## HTML Parsing Logic

The scraper looks for `<span class="wA">` elements with `title` attributes containing pronunciation and translation data in the format: `[pronunciation] translation`.