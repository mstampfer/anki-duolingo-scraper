import requests
from bs4 import BeautifulSoup
import genanki
import os
import re
import random
from gtts import gTTS
import sys
import argparse
import zipfile
import sqlite3
import shutil
import tempfile
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def extract_existing_translations(apkg_path):
    """Extract translation pairs from existing APKG file"""
    translations = {}
    
    if not os.path.exists(apkg_path):
        print(f"No existing APKG file found at {apkg_path}")
        return translations
    
    print(f"Loading existing translations from {apkg_path}...")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Extract APKG (it's a ZIP file)
            with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            db_path = os.path.join(temp_dir, "collection.anki2")
            
            if not os.path.exists(db_path):
                print("No collection.anki2 found in APKG file")
                return translations
            
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Extract notes with their fields
            # Fields are separated by \x1f character in Anki's format
            cursor.execute("SELECT flds FROM notes")
            for row in cursor.fetchall():
                fields = row[0].split('\x1f')  # Split by field separator
                if len(fields) >= 3:  # Target, Pronunciation, English
                    target_word = fields[0].strip()
                    english_translation = fields[2].strip()  # English is the 3rd field
                    if target_word and english_translation and english_translation != "[No translation]":
                        translations[target_word] = english_translation
            
            conn.close()
            print(f"✓ Loaded {len(translations)} existing translations")
            
        except Exception as e:
            print(f"⚠ Error reading APKG file: {e}")
    
    return translations


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape Duolingo vocabulary and create Anki flashcards')
    parser.add_argument('-l', '--language', default='ru', 
                       help='Target language code (ISO 639-1, e.g., ru, es, fr, de). Default: ru (Russian)')
    parser.add_argument('--api-key', 
                       help='Anthropic API key for translating missing words (optional)')
    args = parser.parse_args()
    
    # Language configuration
    lang_code = args.language.lower()
    
    # Language name mapping for common languages
    lang_names = {
        'ru': 'Russian',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'pl': 'Polish',
        'tr': 'Turkish',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'hi': 'Hindi'
    }
    
    lang_name = lang_names.get(lang_code, lang_code.upper())
    
    # Load existing translations from APKG file if it exists
    output_file = f'duolingo_{lang_code}_vocabulary.apkg'
    existing_translations = extract_existing_translations(output_file)
    
    # Initialize Claude API client if available and API key provided
    claude_client = None
    if ANTHROPIC_AVAILABLE and args.api_key:
        try:
            claude_client = anthropic.Anthropic(api_key=args.api_key)
            print("✓ Claude API initialized for translation assistance")
        except Exception as e:
            print(f"⚠ Warning: Failed to initialize Claude API: {e}")
    elif args.api_key and not ANTHROPIC_AVAILABLE:
        print("⚠ Warning: API key provided but anthropic package not installed. Install with: pip install anthropic")
    
    print(f"Starting to scrape Duolingo {lang_name} vocabulary...")

    # Create a model (template) for the vocabulary flashcards
    model_id = random.randrange(1 << 30, 1 << 31)
    vocab_model = genanki.Model(
        model_id,
        f'{lang_name} Vocabulary',
        fields=[
            {'name': 'Target'},
            {'name': 'Pronunciation'},
            {'name': 'English'},
            {'name': 'Audio'}
        ],
        templates=[
            {
                'name': f'{lang_name} to English',
                'qfmt': '{{Target}}<br>{{Audio}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Pronunciation}}<br>{{English}}',
            },
            {
                'name': f'English to {lang_name}',
                'qfmt': '{{English}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Target}}<br>{{Pronunciation}}<br>{{Audio}}',
            }
        ],
        css='.card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }'
    )

    # Create a deck for the flashcards
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, f'Duolingo {lang_name} Vocabulary')

    # Create a directory for audio files
    audio_dir = f'audio_{lang_code}'
    os.makedirs(audio_dir, exist_ok=True)

    # Function to translate using Claude API
    def translate_with_claude(word, target_lang_name, target_lang_code):
        """Translate a word using Claude API"""
        if not claude_client:
            return None
        
        try:
            message = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[
                    {
                        "role": "user", 
                        "content": f"Translate this {target_lang_name} word to English. Provide only the English translation, no explanation: {word}"
                    }
                ]
            )
            translation = message.content[0].text.strip()
            print(f"🤖 Claude translation: {word} → {translation}")
            return translation
        except Exception as e:
            print(f"⚠ Claude API error for '{word}': {e}")
            return None

    # Function to generate audio using gTTS (Google Text-to-Speech)
    def generate_audio(text, filename, lang=lang_code):
        """Generate audio file with 429 error handling"""
        # Only generate audio if file doesn't exist or is empty
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            try:
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(filename)
                print(f"✓ Audio downloaded: {text}")
                return True, False  # (success, is_429)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"HTTP 429 Error: Too Many Requests. Stopping audio generation.")
                    return False, True
                print(f"HTTP Error {e.response.status_code} generating audio for '{text}': {e}")
                return False, False
            except Exception as e:
                print(f"Error generating audio for '{text}': {e}")
                return False, False
        else:
            print(f"• Audio exists: {text}")
        return True, False  # File already exists

    # Scrape the vocabulary page
    url = f'https://duome.eu/vocabulary/en/{lang_code}/skills'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print(f"Fetching vocabulary from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching vocabulary page: {e}")
        sys.exit(1)

    # Find all word entries
    media_files = []
    entries = []
    skip_audio = False  # Flag to track 429 status

    print("Parsing vocabulary entries...")
    # Based on the HTML structure seen in the search results
    for li in soup.select('li'):
        # Look for the wA span which contains the target language word and has title with pronunciation and translation
        wa_span = li.select_one('span.wA')
        if wa_span and wa_span.get('title'):
            target_word = wa_span.text.strip()
            title_text = wa_span['title']

            # Parse the title which contains "[pronunciation] translation"
            match = re.match(r'\[(.*?)\](.*)', title_text)
            if match:
                pronunciation = match.group(1).strip()
                english_translation = match.group(2).strip()
            else:
                pronunciation = ""
                english_translation = title_text.strip()
            
            # Check for existing translation first, then try Claude API if needed
            if not english_translation or english_translation == target_word:
                # Check if we have an existing translation
                if target_word in existing_translations:
                    english_translation = existing_translations[target_word]
                    print(f"📖 Using existing translation: {target_word} → {english_translation}")
                else:
                    # Try Claude API for new translation
                    claude_translation = translate_with_claude(target_word, lang_name, lang_code)
                    if claude_translation:
                        english_translation = claude_translation
                    else:
                        print(f"⚠ No translation found for: {target_word}")
                        english_translation = "[No translation]"

            # Generate audio using Google Text-to-Speech
            audio_filename = f"{audio_dir}/{target_word}.mp3"
            if not skip_audio:
                success, is_429 = generate_audio(target_word, audio_filename)
                if is_429:
                    skip_audio = True
                    audio_filename = None  # Skip remaining audio generation
                elif success:
                    media_files.append(audio_filename)
                else:
                    audio_filename = None
            else:
                audio_filename = None

            entries.append({
                'target': target_word,
                'pronunciation': pronunciation,
                'english': english_translation,
                'audio': audio_filename
            })

    if not entries:
        print("No vocabulary entries found! The website structure might have changed.")
        sys.exit(1)

    print(f"Found {len(entries)} vocabulary entries.")
    print("Creating Anki deck...")

    # Add notes to the deck
    for entry in entries:
        audio_html = f'[sound:{os.path.basename(entry["audio"])}]' if entry['audio'] else ''
        note = genanki.Note(
            model=vocab_model,
            fields=[
                entry['target'],
                entry['pronunciation'],
                entry['english'],
                audio_html
            ]
        )
        deck.add_note(note)

    # Create the Anki package
    package = genanki.Package(deck)
    if media_files:
        package.media_files = media_files

    try:
        package.write_to_file(output_file)
        print(f"Successfully created Anki deck with {len(entries)} vocabulary cards.")
        print(f"Output file: {output_file}")
        print("You can import this deck into Anki using File -> Import.")
    except Exception as e:
        print(f"Error writing Anki package: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
