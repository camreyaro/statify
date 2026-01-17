import sqlite3

DB_PATH = "mood_cache.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS song_emotions (
        song_id TEXT PRIMARY KEY,
        name TEXT,
        artist TEXT,
        emotion TEXT
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

def get_emotion(song_id: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT emotion FROM song_emotions WHERE song_id = ?", (song_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def save_emotion(song_id: str, name: str, artist: str, emotion: str):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO song_emotions (song_id, name, artist, emotion) VALUES (?, ?, ?, ?)",
        (song_id, name, artist, emotion)
    )
    conn.commit()
    cur.close()
    conn.close()
