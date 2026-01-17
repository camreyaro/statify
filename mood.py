import os
import re
import asyncio
from collections import Counter, defaultdict
from transformers import pipeline
from lyricsgenius import Genius
from googletrans import Translator
from mood_store import get_emotion, save_emotion

genius = Genius(os.getenv('GENIUS_TOKEN'))

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base"
)

EMOTION_GROUPS = {
    "joy": "positive",

    "neutral": "neutral",
    "surprise": "neutral",

    "sadness": "negative",
    "anger": "negative",
    "fear": "negative",
    "disgust": "negative"
}

EMOTION_GROUP_VALUE = {
    "positive": 1,
    "neutral": 0,
    "negative": -1
}

def get_lyrics(song_name, artist):
    song = genius.search_song(song_name, artist)

    if song is None:
        return ""

    return asyncio.run(translate(clean_lyrics(song.lyrics)))


def clean_lyrics(raw_lyrics: str) -> str:
    lyrics = re.sub(r"\[.*?\]\n?", "", raw_lyrics)
    lyrics = re.sub(r"\(.*?\)", "", lyrics)
    lyrics = re.sub(r"\n{2,}", "\n", lyrics)
    lyrics = lyrics.strip()

    return lyrics

async def translate(lyrics):
    translator = Translator()
    result = await translator.translate(lyrics, dest='en')
    return result.text

def sentiment_analysis(lyrics, chunk_size=400):
    try:
        chunks = [
            lyrics[i:i + chunk_size]
            for i in range(0, len(lyrics), chunk_size)
        ]

        results = emotion_classifier(chunks)
        emotions = [r['label'] for r in results]

        return max(set(emotions), key=emotions.count)
    except:
        return 'neutral'

def _build_emotion_distribution(songs):
    counter = Counter(song["emotion"] for song in songs)
    total = sum(counter.values())

    return {
        emotion: round((count / total) * 100, 2)
        for emotion, count in counter.items()
    }

def _build_emotion_timeline(songs):
    return [
        {
            "played_at": song["played_at"],
            "value": song["emotion_value"],
            "emotion_group": song["emotion_group"],
            "song": song["name"]
        }
        for song in sorted(songs, key=lambda s: s["played_at"])
    ]

def build_mood(songs):
    enriched_songs = []

    for song in songs:
        song_id = song["id"]
        emotion = get_emotion(song_id)

        if not emotion:
            lyrics = get_lyrics(song["name"], song["artist"])
            emotion = sentiment_analysis(lyrics)
            save_emotion(song_id, song["name"], song["artist"], emotion)

        group = EMOTION_GROUPS.get(emotion, "neutral")
        enriched_songs.append({
            "name": song["name"],
            "artist": song["artist"],
            "played_at": song['played_at'],
            "emotion": emotion,
            "emotion_group": group,
            "emotion_value": EMOTION_GROUP_VALUE[group]
        })

    return {
        "songs": enriched_songs,
        "emotion_distribution": _build_emotion_distribution(enriched_songs),
        "emotion_timeline": _build_emotion_timeline(enriched_songs)
    }