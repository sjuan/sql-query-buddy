"""
Sample Database Setup
Creates a sample database with realistic data for testing.
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os


def create_sample_database(db_path: str = "sample_database.db"):
    """
    Create a sample database with customers, products, orders, and order_items tables.
    
    Args:
        db_path: Path to SQLite database file
    """
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
    
    # Customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            state TEXT,
            city TEXT,
            registration_date DATE,
            total_orders INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0.0
        )
    """)
    
    # Products table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            description TEXT
        )
    """)
    
    # Orders table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            shipping_state TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Order items table
    cursor.execute("""
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
    cursor.execute("CREATE INDEX idx_orders_date ON orders(order_date)")
    cursor.execute("CREATE INDEX idx_order_items_order ON order_items(order_id)")
    cursor.execute("CREATE INDEX idx_order_items_product ON order_items(product_id)")
    cursor.execute("CREATE INDEX idx_customers_state ON customers(state)")
    
    print("Inserting sample data...")
    
    # Sample data
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", 
                   "Ivy", "Jack", "Karen", "Liam", "Mia", "Noah", "Olivia", "Paul", 
                   "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier", "Yara", "Zoe"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", 
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", 
                  "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"]
    
    states = ["California", "New York", "Texas", "Florida", "Illinois", "Pennsylvania", 
              "Ohio", "Georgia", "North Carolina", "Michigan"]
    
    cities = ["Los Angeles", "New York", "Houston", "Miami", "Chicago", "Philadelphia", 
              "Phoenix", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin"]
    
    categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Toys"]
    
    products_data = [
        ("Laptop Pro 15", "Electronics", 1299.99, 50),
        ("Wireless Mouse", "Electronics", 29.99, 200),
        ("Mechanical Keyboard", "Electronics", 149.99, 100),
        ("Cotton T-Shirt", "Clothing", 19.99, 300),
        ("Denim Jeans", "Clothing", 79.99, 150),
        ("Running Shoes", "Clothing", 119.99, 120),
        ("Python Programming", "Books", 49.99, 80),
        ("Data Science Guide", "Books", 59.99, 60),
        ("Garden Tools Set", "Home & Garden", 89.99, 90),
        ("Yoga Mat", "Sports", 34.99, 200),
        ("Basketball", "Sports", 24.99, 150),
        ("Action Figure", "Toys", 14.99, 250),
    ]
    
    # Insert products
    for product_name, category, price, stock in products_data:
        cursor.execute("""
            INSERT INTO products (product_name, category, price, stock_quantity, description)
            VALUES (?, ?, ?, ?, ?)
        """, (product_name, category, price, stock, f"High-quality {product_name}"))
    
    # Insert customers
    customers = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(100):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
        phone = f"555-{random.randint(1000, 9999)}"
        state = random.choice(states)
        city = random.choice(cities)
        reg_date = base_date + timedelta(days=random.randint(0, 365))
        
        cursor.execute("""
            INSERT INTO customers (first_name, last_name, email, phone, state, city, registration_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, state, city, reg_date.strftime("%Y-%m-%d")))
        
        customers.append(cursor.lastrowid)
    
    # Insert orders
    orders = []
    order_date_start = datetime(2024, 1, 1)
    
    for i in range(500):
        customer_id = random.choice(customers)
        order_date = order_date_start + timedelta(days=random.randint(0, 365))
        status = random.choice(["completed", "pending", "shipped", "cancelled"])
        shipping_state = random.choice(states)
        
        # Generate order items
        num_items = random.randint(1, 5)
        total_amount = 0.0
        
        order_items = []
        for _ in range(num_items):
            product_id = random.randint(1, len(products_data))
            quantity = random.randint(1, 3)
            
            # Get product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            unit_price = cursor.fetchone()[0]
            subtotal = unit_price * quantity
            total_amount += subtotal
            
            order_items.append((product_id, quantity, unit_price, subtotal))
        
        # Insert order
        cursor.execute("""
            INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_state)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, order_date.strftime("%Y-%m-%d"), total_amount, status, shipping_state))
        
        order_id = cursor.lastrowid
        orders.append(order_id)
        
        # Insert order items
        for product_id, quantity, unit_price, subtotal in order_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, product_id, quantity, unit_price, subtotal))
    
    # Update customer statistics
    print("Updating customer statistics...")
    cursor.execute("""
        UPDATE customers
        SET total_orders = (
            SELECT COUNT(*) FROM orders WHERE orders.customer_id = customers.customer_id
        ),
        total_spent = (
            SELECT COALESCE(SUM(total_amount), 0) FROM orders 
            WHERE orders.customer_id = customers.customer_id
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Sample database created successfully at {db_path}")
    print(f"   - 100 customers")
    print(f"   - {len(products_data)} products")
    print(f"   - {len(orders)} orders")
    print(f"   - Multiple order items")


if __name__ == "__main__":
    create_sample_database()

