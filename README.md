# 🛒 Photon Cure – Django eCommerce Store

Photon Cure is a full-featured eCommerce web application built with Django. It supports product listings, shopping cart, order management, Razorpay payments, and user authentication, all wrapped in a clean and responsive UI.

---

## 🚀 Features

- 🔐 User registration, login, password reset, and profile management  
- 📦 Product listing, detail view, categories  
- 🛒 Add to cart, quantity updates, remove items  
- 💳 Razorpay payment gateway integration  
- 📧 Email notifications (welcome emails, order updates)  
- 🚚 Order tracking with delivery date range (metro vs non-metro logic)  
- 📊 Admin dashboard for order and product management  
- 📱 Mobile responsive layout  

---

## 🧰 Tech Stack

| Layer           | Technology                    |
|------------------|-------------------------------|
| Backend          | Django, Django REST Framework |
| Frontend         | Django templates + Bootstrap  |
| Payments         | Razorpay API                  |
| Database         | SQLite (dev) / PostgreSQL (prod) |
| Background Tasks | Celery + Redis (for emails)   |
| Hosting          | PythonAnywhere / Railway / etc. |

---

## 🔧 Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/photon_cure.git
cd photon_cure
```

2. **Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. **Install Requirements**

```bash
pip install -r requirements.txt
```

4. **Configure Environment**

Create a `.env` file in the root:

```
DEBUG=True
SECRET_KEY=your_secret_key
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_app_password
```

5. **Run Migrations**

```bash
python manage.py migrate
```

6. **Create Superuser (Admin Login)**

```bash
python manage.py createsuperuser
```

7. **Start the Server**

```bash
python manage.py runserver
```

---

## 🧪 Testing

- Register a new user  
- Browse products, add to cart  
- Checkout using Razorpay test mode  
- Admin access: `/admin/`  
- Track delivery and status from user/order views  

---

## 📂 Project Structure

```
photon_cure/
├── accounts/       # User registration, login, profile
├── products/       # Product models, views, categories
├── cart/           # Add/remove/update cart logic
├── orders/         # Order model, Razorpay, delivery system
├── templates/      # HTML templates (Bootstrap-based)
├── email/          # Email templates (welcome, order status)
├── static/         # Static assets (CSS, JS, images)
└── manage.py
```

---

## 📧 Contact

Created by [Your Name](https://github.com/yourusername)  
Email: your_email@example.com

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
