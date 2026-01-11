import os
import asyncio
from collections import defaultdict
from transformers import pipeline
from lyricsgenius import Genius
from googletrans import Translator

genius = Genius(os.getenv('GENIUS_TOKEN'))

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base"
)

def get_lyrics(song_name, artist):
    song = genius.search_song(song_name, artist)

    if song is None:
        return ""

    return asyncio.run(translate(song.lyrics))

async def translate(lyrics):
    translator = Translator()
    result = await translator.translate(lyrics, dest='en')
    return result.text

def sentiment_analysis(lyrics, chunk_size=400):
    chunks = [
        lyrics[i:i + chunk_size]
        for i in range(0, len(lyrics), chunk_size)
    ]

    results = emotion_classifier(chunks)
    emotions = [r['label'] for r in results]

    return max(set(emotions), key=emotions.count)

def build_mood(songs):
    mood = defaultdict(list)
    for song in songs:
        lyrics = get_lyrics(song['name'], song['artist'])
        emotion = sentiment_analysis(lyrics)
        mood[emotion].append(song)
    return mood