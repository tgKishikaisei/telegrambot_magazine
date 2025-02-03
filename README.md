# Telegram Shop Bot
- A simple Telegram bot built with aiogram and SQLAlchemy that simulates an online store: browsing categories, adding products to a cart, and creating orders.

## Features
- Display Categories & Products
- Reads from data.json to show a list of categories (e.g., Smartphones, Notebooks). Each category has associated products.

## Cart Management

- Add products to the cart
- Update quantities (increase, decrease)
- Remove items or clear the cart
- Calculate the total price 
- Order Creation (FSM)
- Uses a finite state machine to collect user data (e.g., address, promo code). Once the user finishes, the bot creates a new order, clears the cart, and notifies the admin.

## Admin Notifications
The bot can send a message to an admin (via ADMIN_ID) whenever a new order is created.

## SQLAlchemy Models
- Includes models for User, Product, CartItem, Order, and OrderItem to store data in a database.

## Project Structure
- telegrambot_magazine/
- ├── bot.py            # Main bot file with aiogram handlers
- ├── database.py       # Database connection and session management
- ├── models.py         # SQLAlchemy models (User, Product, CartItem, etc.)
- ├── data.json         # Example data with categories & products
- ├── requirements.txt  # List of Python dependencies
- ├── .env              # Stores TELEGRAM_BOT_TOKEN, ADMIN_ID, etc. (not committed)
- └── README.md         # Project description

## Key Files
- bot.py
- Initializes the bot, defines command and callback handlers for categories, cart, and order checkout.

# database.py
- Configures the database connection (e.g., SQLite or PostgreSQL) and provides functions to create database sessions.

# models.py
- Defines SQLAlchemy models for storing users, products, cart items, orders, and order items.

# data.json
- Contains sample categories and products that the bot displays. You can also load them into the database if needed.

# .env
- Holds environment variables such as:

- TELEGRAM_BOT_TOKEN
ADMIN_ID
Other credentials/config as needed
# Installation & Setup
### Clone the repository:


    git clone https://github.com/tgKishikaisei/telegrambot_magazine.git

    cd telegrambot_magazine
- Create a virtual environment (optional but recommended):


    python -m venv venv
    
    source venv/bin/activate  # or "venv\Scripts\activate" on Windows

### Install dependencies:


    pip install -r requirements.txt

### Configure .env:


- TELEGRAM_BOT_TOKEN="123456:ABC-DeF..."
- ADMIN_ID="Your id"
- Optionally add any database credentials if you’re using a non-default DB.

### (Optional) Initialize the database:


### python database.py  # or a custom script to create tables
### Run the bot:


    python bot.py
# Usage
- Start: In Telegram, send /start to the bot. 
- Browse Products: Tap 🛍️ Каталог to see categories and select one to view products. 
- Add to Cart: Tap ➕ Добавить в корзину (Add to Cart). 
- View Cart: Tap 🛒 Корзина to see items and total price. 
- Checkout: Tap 📦 Оформить заказ to finalize your order. The bot may ask for contact info or address (FSM steps). 
- Admin Notification: The bot notifies the admin (ADMIN_ID) with order details upon checkout. 
- Contributing 
- Feel free to fork and submit pull requests. If you find any bugs or have suggestions, open an issue in the repository.

# License
- No specific license is declared by default; you can add an MIT License or other if needed.

