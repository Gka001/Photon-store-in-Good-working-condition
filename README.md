# 🛍️ Photon Cure

**Photon Cure** is a modern, full-stack **Django eCommerce application** for selling products online.  
It includes **user authentication**, **email notifications**, **Celery + Redis for background tasks**, and **payment integration using Razorpay**.

---

## 🚀 Key Features

- 👤 User registration, login & profile management
- 📧 Welcome emails using Celery & Redis
- 🛒 Product listing, cart, and order management
- 💳 Razorpay payment integration
- 📦 Expected delivery date calculation (metro vs non-metro)
- 🧑‍💼 Django Admin for managing orders, users, and products
- 📩 Order status update emails with estimated delivery window
- 🔒 Custom user model for flexibility

---

## 🧰 Tech Stack

| Layer        | Technology               |
|--------------|--------------------------|
| Backend      | Django (Python)          |
| Task Queue   | Celery + Redis           |
| Database     | SQLite (dev) / PostgreSQL (optional) |
| Email        | SMTP (e.g., Gmail)       |
| Frontend     | HTML, Bootstrap (or Tailwind CSS) |
| Payment      | Razorpay                 |

---

## ⚙️ Getting Started

### 1. Clone the Project

```bash
git clone https://github.com/Gka001/photon-cure.git
cd photon_cure

2. Set Up Virtual Environment
bash

python -m venv venv
source venv/bin/activate
3. Install Python Requirements
bash
pip install -r requirements.txt

4. Apply Migrations
bash
python manage.py migrate

5. Start All Services (Django + Celery + Redis)
bash
./start_dev.sh

6. Create Superuser (first time only)
bash
python manage.py createsuperuser

🧪 Testing Email Functionality
Make sure Redis and Celery are running (./start_dev.sh)

Register a new user

Check your email inbox (and spam) for the welcome email

🛑 Stopping the Project
bash
./stop_dev.sh

📝 Developer Notes
📁 Use dev_commands.md for useful Django/Celery/Redis CLI shortcuts


🧪 Test product orders, payments, and delivery dates from the user dashboard


🔄 Automated Git backups via backup_to_git.sh (cron job)

🧑‍💻 Contributing
Fork the repository

Create a new feature branch
git checkout -b feature/your-feature-name

Commit and push your changes

Open a pull request

📄 License
Licensed under the MIT License — free to use and modify.

