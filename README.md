# 🛒 ShopEase - Django E-Commerce Mini Project

A simple Django-based online store built as a mini project.

## 🚀 Features
- Product and Category models
- Django Admin for CRUD operations
- Public Product List and Product Detail pages
- Bootstrap 5 UI with Navbar, Footer and Responsive Layout
- SQLite database connection

## ⚙️ How to Run Locally
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
