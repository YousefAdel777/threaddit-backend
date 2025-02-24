# Threaddit Backend

Threaddit is a Reddit-like platform that allows users to create communities, post content, and engage in discussions. This repository contains the backend for Threaddit, built using **Django REST Framework (DRF)**.

## 🚀 Features
- **User Authentication**: Uses Djoser for token-based authentication.
- **Communities**: Users can create and manage communities.
- **Posts & Comments**: CRUD operations for posts and nested comments.
- **Voting System**: Upvote/downvote for posts and comments.
- **Moderation**: Role-based permissions for moderators.
- **Notifications**: Users receive notifications for interactions.
- **Real-time Updates**: WebSocket support for live interactions.

## 🛠️ Tech Stack
- **Backend**: Django, Django REST Framework (DRF)
- **Database**: PostgreSQL (or SQLite for development)
- **Authentication**: dj-rest-auth + JWT
- **Caching**: Redis
- **Task Queue**: Celery + Redis (for async tasks)
- **WebSockets**: Django Channels
- **Docker**: Containerization

## 📂 Project Structure
```
threaddit-backend/
│── api/                # DRF API views and serializers
│── accounts/           # User authentication & profiles
│── communities/        # Community-related models & views
│── posts/              # Post and comment management
│── notifications/      # Notification system
│── media/              # Uploaded files & images
│── .env                # Environment variables
│── db.sqlite3          # Local SQLite database (ignored in production)
│── Dockerfile          # Docker container setup
│── docker-compose.yml  # Docker services configuration
│── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## 🔧 Installation & Setup
### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/threaddit-backend.git
cd threaddit-backend
```

### 2️⃣ Create & activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set up environment variables
Create a `.env` file in the project root and add:
```ini
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/threaddit_db
REDIS_URL=redis://localhost:6379
```

### 5️⃣ Apply database migrations
```bash
python manage.py migrate
```

### 6️⃣ Create a superuser
```bash
python manage.py createsuperuser
```

### 7️⃣ Run the development server
```bash
python manage.py runserver
```

### 8️⃣ Run Celery (optional, for async tasks)
```bash
celery -A threaddit worker --loglevel=info
```

## 🐳 Docker Setup (Optional)
```bash
docker-compose up --build
```