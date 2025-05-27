# Duolingo Vocabulary Scraper for Anki

A multilingual vocabulary scraper that extracts words from Duolingo via duome.eu and creates Anki flashcard decks with audio pronunciations.

## Features

- 🌍 **Multilingual Support**: Scrape vocabulary for 14+ languages
- 🔊 **Audio Pronunciations**: Automatic TTS audio generation using Google Text-to-Speech
- 📚 **Dual-sided Flashcards**: Target Language ↔ English with pronunciation guides
- 🚀 **Easy Setup**: One-command installation with detailed setup instructions
- 📊 **Progress Logging**: Real-time feedback on audio downloads and processing
- 🔄 **Incremental Updates**: Skip existing audio files for faster re-runs

## Quick Start

```bash
# Clone the repository
git clone https://github.com/mstampfer/anki-duolingo-scraper.git
cd anki-duolingo-scraper

# Set up environment (see setup.md for detailed instructions)
pip install -r requirements.txt

# Run scraper (defaults to Russian)
python scraper.py

# Or specify a different language
python scraper.py -l es  # Spanish
python scraper.py -l fr  # French
python scraper.py -l de  # German
```

## Supported Languages

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| `ru` | Russian | `es` | Spanish | `fr` | French |
| `de` | German | `it` | Italian | `pt` | Portuguese |
| `nl` | Dutch | `pl` | Polish | `tr` | Turkish |
| `ja` | Japanese | `ko` | Korean | `zh` | Chinese |
| `ar` | Arabic | `hi` | Hindi | | |

## Usage

```bash
# Show help
python scraper.py --help

# Default (Russian)
python scraper.py

# Specify language with ISO 639-1 code
python scraper.py -l <language_code>

# Examples
python scraper.py -l es  # Spanish
python scraper.py -l ja  # Japanese
python scraper.py -l de  # German
```

## Output

- **Anki Deck**: `duolingo_{language_code}_vocabulary.apkg`
- **Audio Files**: `audio_{language_code}/*.mp3`

Import the `.apkg` file into Anki using `File → Import`.

## Requirements

- Python 3.7+
- Internet connection (for scraping and TTS)
- See `requirements.txt` for package dependencies

## Installation

### Option 1: Using pip/venv
```bash
python -m venv duolingo_scraper_env
source duolingo_scraper_env/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Option 2: Using conda/mamba
```bash
mamba create -n duolingo_scraper python=3.9
mamba activate duolingo_scraper
pip install -r requirements.txt
```

For detailed setup instructions, see [`setup.md`](setup.md).

## How It Works

1. **Scrapes** vocabulary from `duome.eu/vocabulary/en/{language}/skills`
2. **Extracts** target language words, pronunciations, and English translations
3. **Generates** audio files using Google Text-to-Speech
4. **Creates** Anki deck with dual-sided flashcards and embedded audio

## Example Output

```
Starting to scrape Duolingo Spanish vocabulary...
Fetching vocabulary from https://duome.eu/vocabulary/en/es/skills...
Parsing vocabulary entries...
✓ Audio downloaded: hola
✓ Audio downloaded: gracias
• Audio exists: adiós
✓ Audio downloaded: por favor
Found 847 vocabulary entries.
Creating Anki deck...
Successfully created Anki deck with 847 vocabulary cards.
Output file: duolingo_es_vocabulary.apkg
```

## Error Handling

- **Rate Limiting**: Gracefully handles Google TTS 429 errors
- **Network Issues**: Robust error handling for connectivity problems
- **Missing Data**: Validates vocabulary extraction and reports issues
- **File Management**: Incremental audio generation and cleanup

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

- **SSL Errors**: Upgrade pip with `pip install --upgrade pip`
- **Audio Issues**: Ensure internet connection for Google TTS
- **Import Errors**: Check that all dependencies are installed
- **Website Changes**: duome.eu structure changes may require updates

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- [duome.eu](https://duome.eu) for providing Duolingo vocabulary data
- [genanki](https://github.com/kerrickstaley/genanki) for Anki deck generation
- [gTTS](https://github.com/pndurette/gTTS) for Google Text-to-Speech integration

## Support

If you encounter issues or have questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review [`setup.md`](setup.md) for detailed installation help
3. Open an issue on GitHub with detailed error information

---

⭐ **Star this repository** if you find it helpful for your language learning journey!