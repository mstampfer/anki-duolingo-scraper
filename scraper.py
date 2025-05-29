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
    """Extract translation pairs and sentence data from existing APKG file"""
    translations = {}
    sentence_data = {}
    
    if not os.path.exists(apkg_path):
        print(f"No existing APKG file found at {apkg_path}")
        return translations, sentence_data
    
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
                return translations, sentence_data
            
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Extract notes with their fields
            # Fields are separated by \x1f character in Anki's format
            cursor.execute("SELECT flds FROM notes")
            for row in cursor.fetchall():
                fields = row[0].split('\x1f')  # Split by field separator
                if len(fields) >= 3:  # Target, Pronunciation, English (minimum for old format)
                    target_word = fields[0].strip()
                    english_translation = fields[2].strip()  # English is the 3rd field
                    if target_word and english_translation and english_translation != "[No translation]":
                        translations[target_word] = english_translation
                        
                        # Check if this is the new format with sentence data (7 fields)
                        if len(fields) >= 7:
                            example_sentence = fields[4].strip() if fields[4] else ''
                            sentence_translation = fields[6].strip() if fields[6] else ''
                            if example_sentence and sentence_translation:
                                sentence_data[target_word] = {
                                    'example': example_sentence,
                                    'translation': sentence_translation
                                }
            
            conn.close()
            print(f"✓ Loaded {len(translations)} existing translations and {len(sentence_data)} sentence examples")
            
        except Exception as e:
            print(f"⚠ Error reading APKG file: {e}")
    
    return translations, sentence_data


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
    existing_translations, existing_sentence_data = extract_existing_translations(output_file)
    
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
            {'name': 'Audio'},
            {'name': 'ExampleSentence'},
            {'name': 'SentenceAudio'},
            {'name': 'SentenceTranslation'}
        ],
        templates=[
            {
                'name': f'{lang_name} to English',
                'qfmt': '{{Target}}<br>{{Audio}}<br><br><div style="font-size: 14px; font-style: italic; color: #666;">{{ExampleSentence}}</div><br>{{SentenceAudio}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Pronunciation}}<br>{{English}}<br><br><div style="font-size: 14px; color: #444;">{{SentenceTranslation}}</div>',
            },
            {
                'name': f'English to {lang_name}',
                'qfmt': '{{English}}<br><br><div style="font-size: 14px; font-style: italic; color: #666;">{{SentenceTranslation}}</div>',
                'afmt': '{{FrontSide}}<hr id="answer">{{Target}}<br>{{Pronunciation}}<br>{{Audio}}<br><br><div style="font-size: 14px; color: #444;">{{ExampleSentence}}</div><br>{{SentenceAudio}}',
            }
        ],
        css='.card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }'
    )

    # Create a deck for the flashcards
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, f'Duolingo {lang_name} Vocabulary')

    # Create directories for audio files
    audio_dir = f'audio_{lang_code}'
    sentence_audio_dir = f'audio_{lang_code}_sentences'
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(sentence_audio_dir, exist_ok=True)

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

    # Function to generate example sentence using Claude API
    def generate_example_sentence(word, target_lang_name, target_lang_code, english_translation):
        """Generate an example sentence using Claude API"""
        if not claude_client:
            return None, None
        
        try:
            message = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[
                    {
                        "role": "user", 
                        "content": f"Create a simple {target_lang_name} sentence using the word '{word}' (meaning: {english_translation}). Then provide the English translation of that sentence. Format your response exactly as:\n\n{target_lang_name} sentence: [sentence]\nEnglish translation: [translation]\n\nUse proper grammar and keep it simple."
                    }
                ]
            )
            response = message.content[0].text.strip()
            
            # Parse the response to extract both sentences
            lines = response.split('\n')
            target_sentence = None
            english_sentence = None
            
            for line in lines:
                line = line.strip()
                if line.lower().startswith(f'{target_lang_name.lower()} sentence:') or line.lower().startswith('sentence:'):
                    target_sentence = line.split(':', 1)[1].strip()
                elif line.lower().startswith('english translation:') or line.lower().startswith('translation:'):
                    english_sentence = line.split(':', 1)[1].strip()
            
            if target_sentence and english_sentence:
                print(f"🎯 Claude sentence: {target_sentence} → {english_sentence}")
                return target_sentence, english_sentence
            else:
                print(f"⚠ Could not parse sentence response for '{word}'")
                return None, None
                
        except Exception as e:
            print(f"⚠ Claude API error generating sentence for '{word}': {e}")
            return None, None

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

    # Function to generate sentence audio using gTTS
    def generate_sentence_audio(sentence, filename, lang=lang_code):
        """Generate audio file for example sentence with 429 error handling"""
        # Only generate audio if file doesn't exist or is empty
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            try:
                tts = gTTS(text=sentence, lang=lang, slow=False)
                tts.save(filename)
                print(f"🔊 Sentence audio downloaded: {sentence[:50]}...")
                return True, False  # (success, is_429)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"HTTP 429 Error: Too Many Requests. Stopping sentence audio generation.")
                    return False, True
                print(f"HTTP Error {e.response.status_code} generating sentence audio for '{sentence[:30]}...': {e}")
                return False, False
            except Exception as e:
                print(f"Error generating sentence audio for '{sentence[:30]}...': {e}")
                return False, False
        else:
            print(f"• Sentence audio exists: {sentence[:50]}...")
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

            # Generate example sentence using Claude API (only if translation is available)
            example_sentence = None
            sentence_translation = None
            sentence_audio_filename = None
            
            if english_translation and english_translation != "[No translation]":
                # Check for existing sentence data first
                if target_word in existing_sentence_data:
                    example_sentence = existing_sentence_data[target_word]['example']
                    sentence_translation = existing_sentence_data[target_word]['translation']
                    print(f"📝 Using existing sentence: {target_word}")
                elif claude_client:
                    # Generate new sentence with Claude API
                    example_sentence, sentence_translation = generate_example_sentence(target_word, lang_name, lang_code, english_translation)
                
                # Generate sentence audio if sentence was created
                if example_sentence and not skip_audio:
                    sentence_audio_filename = f"{sentence_audio_dir}/{target_word}_sentence.mp3"
                    success, is_429 = generate_sentence_audio(example_sentence, sentence_audio_filename)
                    if is_429:
                        skip_audio = True
                        sentence_audio_filename = None
                    elif success:
                        media_files.append(sentence_audio_filename)
                    else:
                        sentence_audio_filename = None

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
                'audio': audio_filename,
                'example_sentence': example_sentence or '',
                'sentence_audio': sentence_audio_filename,
                'sentence_translation': sentence_translation or ''
            })

    if not entries:
        print("No vocabulary entries found! The website structure might have changed.")
        sys.exit(1)

    print(f"Found {len(entries)} vocabulary entries.")
    print("Creating Anki deck...")

    # Add notes to the deck
    for entry in entries:
        audio_html = f'[sound:{os.path.basename(entry["audio"])}]' if entry['audio'] else ''
        sentence_audio_html = f'[sound:{os.path.basename(entry["sentence_audio"])}]' if entry['sentence_audio'] else ''
        note = genanki.Note(
            model=vocab_model,
            fields=[
                entry['target'],
                entry['pronunciation'],
                entry['english'],
                audio_html,
                entry['example_sentence'],
                sentence_audio_html,
                entry['sentence_translation']
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
