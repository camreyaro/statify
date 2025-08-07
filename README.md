# ![Statify Banner](./images/banner.png)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Spotify](https://img.shields.io/badge/Spotify-1ED760?style=for-the-badge&logo=spotify&logoColor=white)

# 🎵 Statify

**Statify** is a super simple and lightweight Python-based application that uses **FastAPI** and **httpx** to provide personalized music statistics through a RESTful API.

---

## 🚀 Technologies

- 🐍 Python 3.10+
- ⚡ FastAPI
- 🌐 httpx

---

## 📦 Available Endpoints

| Method | Route                   | Description                            |
|--------|-------------------------|----------------------------------------|
| GET    | `/user-data`            | Retrieves user profile information     |
| GET    | `/top-tracks`           | Retrieves user's top tracks            |
| GET    | `/top-artists`          | Retrieves user's top artists           |
| GET    | `/top-tracks-by-artist` | Retrieves top tracks grouped by artist |

---

## 🛠️ Installation & Run

```bash
# Clone the repository
git clone https://github.com/camreyaro/statify.git
cd statify

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload
```

<p><b><small> Made with 💜 by @camreyaro</small></b></p>