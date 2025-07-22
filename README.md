
# 🛍️ Photon Cure

**Photon Cure** is a Django-based eCommerce store built for selling products online.  
It supports background task processing using **Celery** and **Redis**, and includes features like user registration, email notifications, and profile management.

---

## 🚀 Features

- ✅ User registration & login
- ✅ Welcome email via Celery & Redis
- ✅ Custom user model
- ✅ Profile editing
- 🛒 Product & order management (in progress)
- 💳 Razorpay integration (coming soon)

---

## ⚙️ Tech Stack

- **Backend**: Django, Python
- **Async Tasks**: Celery with Redis as broker
- **Database**: SQLite (default, replaceable with PostgreSQL)
- **Email**: SMTP backend (e.g., Gmail)
- **Frontend**: HTML, Bootstrap (or Tailwind optional)

---

## 🧰 Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd photon_cure
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Migrations
```bash
python manage.py migrate
```

### 5. Start Development Environment
```bash
./start_dev.sh
```

### 6. Create Superuser (first time only)
```bash
python manage.py createsuperuser
```

---

## 🛑 Stop Development Environment

```bash
./stop_dev.sh
```

---

## 📘 Developer Notes

For detailed CLI commands (Celery, Redis, Django), see [`dev_commands.md`](./dev_commands.md).

---

## 📬 Welcome Email Testing

To test welcome email:
- Make sure Redis, Celery, and Django are running (`./start_dev.sh`)
- Register a new user
- Check inbox for welcome email

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch
5. Create a pull request

---

## 📄 License

MIT License — free to use and modify.

---

**Made with ❤️ using Django**
