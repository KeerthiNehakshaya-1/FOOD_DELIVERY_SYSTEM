# 🍴 FoodFlow - Food Delivery Management System

FoodFlow is a web-based Food Delivery Management System developed using **Flask and Oracle Database**. The system manages customers, restaurants, menu items, food orders, payments, delivery partners, and deliveries through separate role-based interfaces.

The project provides three main user roles:

- 👨‍💼 **Admin**
- 👤 **Customer**
- 🛵 **Delivery Partner**

The system demonstrates database management concepts such as primary keys, foreign keys, constraints, relationships, SQL queries, transactions, and database connectivity through a Flask application.

---

## 🎯 Objectives

The main objectives of FoodFlow are:

- To manage customers and their information.
- To manage restaurants and menu items.
- To allow customers to place food orders.
- To maintain detailed order information.
- To manage different payment methods and payment statuses.
- To assign delivery partners to orders.
- To track the delivery status of orders.
- To provide an admin dashboard for monitoring the complete system.
- To demonstrate practical implementation of a relational database using Oracle.

---

## ✨ Key Features

### 👨‍💼 Admin

The administrator can:

- View the system dashboard.
- View database statistics.
- Manage customers.
- Manage restaurants.
- Manage menu items.
- View food orders.
- View order details.
- Manage payments.
- Process eligible refunds.
- Manage delivery partners.
- Assign delivery partners to orders.
- Monitor delivery status.
- Update order status.
- View restaurant order statistics using a line graph.

### 👤 Customer

Customers can:

- Enter their details.
- Access the customer interface.
- View available restaurants.
- View restaurant menus.
- Select food items and quantities.
- Choose a payment method.
- Place orders.
- View previous orders.
- View order details.
- Cancel eligible orders.
- Track the status of their orders.

### 🛵 Delivery Partner

Delivery partners can:

- Log in using their assigned credentials.
- View their profile information.
- View assigned deliveries.
- Update delivery status.
- Mark an order as picked up.
- Start delivery.
- Mark an order as delivered.
- Cancel a delivery when required.

The delivery workflow follows:

```text
Assigned
    ↓
Picked Up
    ↓
Out for Delivery
    ↓
Delivered

```

---

## 🗄️ Database Design

FoodFlow uses an Oracle relational database containing 8 main tables.

- Tables
- CUSTOMER
- RESTAURANT
- MENU_ITEM
- FOOD_ORDER
- ORDER_DETAIL
- PAYMENT
- DELIVERY_PARTNER
- DELIVERY

### Relationships

```text
CUSTOMER
    │
    │ 1 : N
    ▼
FOOD_ORDER
    │
    ├──────────────► ORDER_DETAIL ◄────────────── MENU_ITEM
    │                    N : 1
    │
    ├──────────────► PAYMENT
    │                    1 : 1
    │
    └──────────────► DELIVERY ◄────────────── DELIVERY_PARTNER
                         N : 1
```
### additional relationships
```text
RESTAURANT
    │
    ├──────────────► MENU_ITEM
    │                    1 : N
    │
    └──────────────► FOOD_ORDER
                         1 : N
```

---

## 📋 Database Tables

| Table | Purpose |
|---|---|
| `CUSTOMER` | Stores customer information |
| `RESTAURANT` | Stores restaurant information |
| `MENU_ITEM` | Stores food items offered by restaurants |
| `FOOD_ORDER` | Stores customer orders |
| `ORDER_DETAIL` | Stores individual items within an order |
| `PAYMENT` | Stores payment information |
| `DELIVERY_PARTNER` | Stores delivery partner information |
| `DELIVERY` | Stores delivery assignments and status |

## 💳 Payment Workflow

FoodFlow supports multiple payment methods:

- Cash
- UPI
- Card
- Net Banking

Payment statuses include:

- Pending
- Paid
- Failed
- Refunded
- Cancelled

### Cash Payment

Cash on Delivery initially remains:

Pending

When the order is successfully delivered:

Pending → Paid

If the customer cancels before payment:

Pending → Cancelled

### Online Payment

For online payments:

UPI / Card / Net Banking
            ↓
           Paid

If a paid online order is cancelled, the payment remains Paid until the administrator processes the refund:

Paid → Refunded

This keeps the cancellation and refund processes separate.

---

## 🚚 Delivery Workflow

Delivery status is managed separately from the order status.
```text
Assigned
    ↓
Picked Up
    ↓
Out for Delivery
    ↓
Delivered
```

Possible cancellation:
```text
Assigned / Picked Up / Out for Delivery
                ↓
            Cancelled
```

The delivery partner cannot directly modify payment status.

When a delivery is marked as Delivered, the corresponding food order is also updated to Delivered, and the payment is marked as Paid.

---

## 📊 Admin Dashboard

The administrator dashboard provides an overview of the database through statistics such as:

- Customers
- Restaurants
- Menu Items
- Orders
- Order Details
- Payments
- Delivery Partners
- Deliveries

The dashboard also contains a Restaurant Statistics Line Graph, which displays daily order performance for restaurants over the recent seven-day period.
```text
Restaurant Statistics
        │
        ▼
Daily Order Count
        │
        ▼
Line Graph
```

This provides a visual way to compare restaurant order activity.

---

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js
### Backend
- Python
- Flask
### Database
- Oracle Database
### Database Connectivity
- Python oracledb
### Development Tools
- Visual Studio Code
- Git
- GitHub
- PowerShell

---

## 📁 Project Structure
```text
FOOD_DELIVERY/
│
├── app.py
│
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    │
    ├── login.html
    ├── index.html
    │
    ├── customers.html
    ├── restaurants.html
    ├── menu.html
    ├── orders.html
    ├── order_details.html
    ├── payments.html
    ├── delivery_partners.html
    ├── deliveries.html
    └── update_order.html
    │
    ├── customer_details.html
    ├── customer_home.html
    ├── customer_orders.html
    ├── place_order.html
    ├── order_success.html
    └── order_error.html
    │
    └── delivery/
        └── dashboard.html
```

---

## ⚙️ Requirements

Before running the project, make sure the following are installed:

- Python 3.x
- Flask
- Oracle Database
- Oracle Database user/schema
- Python oracledb package
- A web browser

Install the required Python packages using:

pip install flask oracledb

---

## 🔧 Database Setup

Create the required Oracle database schema and tables.

The application expects an Oracle database connection using the following structure:

Host: localhost
Port: 1521
Service: freepdb1

Create the FOOD_DELIVERY database user and configure the required tables and constraints before running the Flask application.

Note: Database passwords and other credentials should not be published in the GitHub repository.

---

## ▶️ Running the Project

Clone the repository:

git clone https://github.com/KeerthiNehakshaya-1/FOOD_DELIVERY_SYSTEM.git

Move into the project directory:

cd FOOD_DELIVERY_SYSTEM

Install dependencies:

pip install flask oracledb

Make sure the Oracle Database is running and the database configuration is available.

Start the Flask application:

python app.py

The application will run locally at:

http://127.0.0.1:5000

Open the address in a web browser.

---

## 🔐 User Roles

### Admin

The admin interface provides complete management access to the system.

### Customer

Customers can browse restaurants, order food, view their orders, and cancel eligible orders.

### Delivery Partner

Delivery partners can view assigned deliveries and update delivery progress.

---

## 🔄 Overall System Flow

```text
                    FoodFlow
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      Admin         Customer       Delivery
        │              │            Partner
        │              │              │
        ▼              ▼              ▼
   Management      Place Order     View Delivery
        │              │              │
        ▼              ▼              ▼
   Orders/Pay.      Payment       Update Status
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Oracle Database
```

---

### 🔒 Security Considerations

The application uses role-based access control for:

- Admin
- Customer
- Delivery Partner

Protected pages are accessible according to the logged-in user's role.

Sensitive database credentials should be stored securely and should not be committed to GitHub.

---

## 🚀 Future Scope

The system can be extended with:

- Online payment gateway integration
- Real-time delivery tracking using maps
- Restaurant owner login and management
- Customer ratings and reviews
- Food recommendations based on customer preferences
- Order notifications through email or SMS
- Advanced analytics for restaurant performance
- Deployment to a cloud platform

---

## 🎓 Academic Concepts Demonstrated

This project demonstrates practical implementation of:

- Relational Database Management Systems
- Entity relationships
- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- SQL queries
- Joins
- Aggregate functions
- Transactions
- CRUD operations
- Database connectivity
- Role-based access
- Web application development

---

## 📌 Project Status

- ✅ Database Design
- ✅ Oracle Database Implementation
- ✅ Flask Backend
- ✅ Admin Module
- ✅ Customer Module
- ✅ Delivery Partner Module
- ✅ Payment Management
- ✅ Delivery Management
- ✅ Restaurant Statistics
- ✅ Frontend Styling
- ✅ GitHub Repository

**Project Status: Completed** 🎉