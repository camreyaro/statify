import os
import asyncio
from collections import Counter
from groq import Groq
from lyricsgenius import Genius
from googletrans import Translator
from mood_store import get_emotion, save_emotion

genius = Genius(os.getenv('GENIUS_TOKEN'), verbose=False, remove_section_headers=True)
grok = Groq(
    api_key=os.getenv('GROK_KEY'),
)

VALID_EMOTIONS = ['happy', 'sad', 'angry', 'nostalgic', 'romantic', 'energetic', 'calm', 'neutral']

EMOTION_GROUPS = {
    'happy': 'positive',
    'romantic': 'positive',
    'energetic': 'positive',

    'calm': 'neutral',
    'neutral': 'neutral',
    'nostalgic': 'neutral',

    'sad': 'negative',
    'angry': 'negative',
}

EMOTION_GROUP_VALUE = {
    'positive': 1,
    'neutral': 0,
    'negative': -1
}

def get_lyrics(song_name, artist):
    song = genius.search_song(song_name, artist)

    if song is None:
        return ''

    return asyncio.run(translate(song.lyrics))

async def translate(lyrics):
    translator = Translator()
    result = await translator.translate(lyrics, dest='en')
    return result.text

def sentiment_analysis_ai(name, artist, lyrics):
    messages = [
        {
            'role': 'system',
            'content': (
                'You are a music emotion classifier.\n'
                'Your task is to output EXACTLY ONE word: the emotion.\n'
                'Valid outputs:\n'
                'happy, sad, angry, nostalgic, romantic, energetic, calm, neutral.\n\n'

                'Rules:\n'
                '- Do NOT explain your choice.\n'
                '- Do NOT add punctuation.\n'
                '- Do NOT add quotes.\n'
                '- Do NOT add newlines.\n'
                '- If you output anything else, the answer is invalid.\n\n'
                
                'You must classify the OVERALL emotional experience of the song, '
                'prioritizing sound, energy, rhythm, and vibe over lyrics when there is a conflict.\n\n'

                'Romantic should ONLY be used if romance is the dominant and almost exclusive emotion, '
                'and the song is emotionally intimate, soft or calm.\n'
                'If a song is energetic, upbeat, aggressive, or danceable, it must NOT be classified as romantic, '
                'even if the lyrics talk about love or relationships.\n\n'

                'Use the artist, song title, and cultural context to infer musical style and energy.\n\n'

                'Return ONLY one of these emotions:\n'
                'happy, sad, angry, nostalgic, romantic, energetic, calm, neutral.'
            )
        },
        {
            'role': 'user',
            'content': (
                f'Artist: {artist}\n'
                f'Song: {name}\n\n'
                f'Lyrics: {lyrics}'
            )
        }
    ]

    response = grok.chat.completions.create(
        model='llama-3.3-70b-versatile',
        messages=messages
    )

    return response.choices[0].message.content


def _build_emotion_distribution(songs):
    counter = Counter(song['emotion'] for song in songs)
    total = sum(counter.values())

    return {
        emotion: round((count / total) * 100, 2)
        for emotion, count in counter.items()
    }


def _build_emotion_timeline(songs):
    return [
        {
            'played_at': song['played_at'],
            'value': song['emotion_value'],
            'emotion_group': song['emotion_group'],
            'song': song['name']
        }
        for song in sorted(songs, key=lambda s: s['played_at'])
    ]


def build_mood(songs):
    enriched_songs = []

    for song in songs:
        song_id = song['id']
        emotion = get_emotion(song_id)

        if not emotion:
            lyrics = get_lyrics(song['name'], song['artist'])

            emotion = sentiment_analysis_ai(song['name'], song['artist'], lyrics).lower()
            if emotion not in VALID_EMOTIONS:
                emotion = 'neutral'

            print(f"{song['name']} - {song['artist']} ---> {emotion}")
            save_emotion(song_id, song['name'], song['artist'], emotion)

        group = EMOTION_GROUPS.get(emotion, 'neutral')
        enriched_songs.append({
            'name': song['name'],
            'artist': song['artist'],
            'played_at': song['played_at'],
            'emotion': emotion,
            'emotion_group': group,
            'emotion_value': EMOTION_GROUP_VALUE[group]
        })

    return {
        'songs': enriched_songs,
        'emotion_distribution': _build_emotion_distribution(enriched_songs),
        'emotion_timeline': _build_emotion_timeline(enriched_songs)
    }
