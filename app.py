from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from functools import wraps
import os
import psycopg2


app = Flask(__name__)

# Used for Flask sessions.
app.secret_key = "foodflow_secret_key_2026"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set."
        )

    return psycopg2.connect(database_url)


# =========================================================
# DATABASE HELPER
# =========================================================

def get_next_id(cursor, table_name, column_name):

    cursor.execute(
        f"""
        SELECT COALESCE(MAX({column_name}), 0) + 1
        FROM {table_name}
        """
    )

    return cursor.fetchone()[0]


# =========================================================
# ROLE ACCESS DECORATORS
# =========================================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if session.get("role") != "admin":
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def customer_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if session.get("role") != "customer":
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def delivery_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if session.get("role") != "delivery":
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# COMMON LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # CUSTOMERS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                Customer_ID,
                Name,
                Email
            FROM CUSTOMER
            ORDER BY Customer_ID
            """
        )

        customers = cursor.fetchall()

        # -------------------------------------------------
        # DELIVERY PARTNERS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                Partner_ID,
                Name
            FROM DELIVERY_PARTNER
            ORDER BY Partner_ID
            """
        )

        partners = cursor.fetchall()

        return render_template(
            "login.html",
            customers=customers,
            partners=partners
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/login/admin", methods=["POST"])
def admin_login():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    # One fixed admin account for the project.

    if username == "admin" and password == "admin123":

        session.clear()

        session["role"] = "admin"

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "login.html",
        customers=[],
        partners=[],
        error="Invalid admin username or password."
    )


# =========================================================
# CUSTOMER ACCESS
# =========================================================

@app.route("/customer/details", methods=["GET", "POST"])
def customer_details():

    if request.method == "GET":
        return render_template("customer_details.html")

    # Get customer details from form
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    # Validate required fields
    if not name or not email or not phone or not address:
        return render_template(
            "customer_details.html",
            error="Please fill in all customer details."
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # -------------------------------------------------
        # CHECK WHETHER CUSTOMER ALREADY EXISTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                Customer_ID,
                Name,
                Email,
                Phone,
                Address
            FROM CUSTOMER
            WHERE Email = %s
               OR Phone = %s
            """,
            (email, phone)
        )

        existing_customer = cursor.fetchone()

        # -------------------------------------------------
        # EXISTING CUSTOMER
        # -------------------------------------------------

        if existing_customer:

            customer_id = existing_customer[0]

            session.clear()

            session["role"] = "customer"
            session["customer_id"] = customer_id
            session["customer_name"] = existing_customer[1]

            return redirect(url_for("customer_home"))

        # -------------------------------------------------
        # NEW CUSTOMER
        # -------------------------------------------------

        customer_id = get_next_id(
            cursor,
            "CUSTOMER",
            "Customer_ID"
        )

        cursor.execute(
            """
            INSERT INTO CUSTOMER
            (
                Customer_ID,
                Name,
                Email,
                Phone,
                Address
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                customer_id,
                name,
                email,
                phone,
                address
            )
        )

        connection.commit()

        session.clear()

        session["role"] = "customer"
        session["customer_id"] = customer_id
        session["customer_name"] = name

        return redirect(url_for("customer_home"))

    except Exception as error_message:

        connection.rollback()

        print(
            "CUSTOMER DETAILS ERROR:",
            error_message
        )

        return render_template(
            "customer_details.html",
            error="Unable to save customer details. Please check your information."
        )

    finally:

        cursor.close()
        connection.close()

# =========================================================
# DELIVERY PARTNER LOGIN
# =========================================================

@app.route("/login/delivery", methods=["POST"])
def delivery_login():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if not username or not password:

        return render_template(
            "login.html",
            customers=[],
            partners=[],
            error="Please enter delivery username and password."
        )

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Partner_ID,
                Name
            FROM DELIVERY_PARTNER
            WHERE Login_Username = %s
              AND Login_Password = %s
            """,
            (
                username,
                password
            )
        )

        partner = cursor.fetchone()

        if partner is None:

            return render_template(
                "login.html",
                customers=[],
                partners=[],
                error="Invalid delivery username or password."
            )

        session.clear()

        session["role"] = "delivery"
        session["partner_id"] = partner[0]
        session["partner_name"] = partner[1]

        return redirect(
            url_for("delivery_dashboard")
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            "SELECT COUNT(*) FROM CUSTOMER"
        )
        customers = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM RESTAURANT"
        )
        restaurants = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM MENU_ITEM"
        )
        menu_items = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM FOOD_ORDER"
        )
        orders = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM ORDER_DETAIL"
        )
        order_details = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM PAYMENT"
        )
        payments = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM DELIVERY_PARTNER"
        )
        delivery_partners = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM DELIVERY"
        )
        deliveries = cursor.fetchone()[0]


        # =================================================
        # RECENT ORDERS
        # =================================================

        cursor.execute(
            """
            SELECT
                O.Order_ID,
                C.Name,
                R.Restaurant_Name,
                O.Total_Amount,
                O.Order_Status
            FROM FOOD_ORDER O
            JOIN CUSTOMER C
                ON O.Customer_ID = C.Customer_ID
            JOIN RESTAURANT R
                ON O.Restaurant_ID = R.Restaurant_ID
            ORDER BY O.Order_ID DESC
            FETCH FIRST 5 ROWS ONLY
            """
        )

        recent_orders = cursor.fetchall()


        # =================================================
        # RESTAURANT ORDER STATISTICS
        # =================================================

        cursor.execute(
            """
            SELECT
                R.Restaurant_ID,
                R.Restaurant_Name,
                O.Order_Date::date AS Order_Day,
                COUNT(O.Order_ID) AS Order_Count
            FROM RESTAURANT R
            LEFT JOIN FOOD_ORDER O
                ON R.Restaurant_ID = O.Restaurant_ID
                AND O.Order_Date >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY
                R.Restaurant_ID,
                R.Restaurant_Name,
                O.Order_Date::date
            ORDER BY
                R.Restaurant_ID,
                Order_Day
            """
        )

        restaurant_statistics = cursor.fetchall()


        # =================================================
        # SEND DATA TO DASHBOARD
        # =================================================

        return render_template(
            "index.html",
            customers=customers,
            restaurants=restaurants,
            menu_items=menu_items,
            orders=orders,
            order_details=order_details,
            payments=payments,
            delivery_partners=delivery_partners,
            deliveries=deliveries,
            recent_orders=recent_orders,
            restaurant_statistics=restaurant_statistics
        )

    finally:

        cursor.close()
        connection.close()

# =========================================================
# ADMIN CUSTOMERS
# =========================================================

@app.route("/admin/customers")
@admin_required
def customers_page():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Customer_ID,
                Name,
                Email,
                Phone,
                Address
            FROM CUSTOMER
            ORDER BY Customer_ID
            """
        )

        customers = cursor.fetchall()

        return render_template(
            "customers.html",
            customers=customers
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN RESTAURANTS
# =========================================================

@app.route("/admin/restaurants")
@admin_required
def restaurants_page():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Restaurant_ID,
                Restaurant_Name,
                Location,
                Phone
            FROM RESTAURANT
            ORDER BY Restaurant_ID
            """
        )

        restaurants = cursor.fetchall()

        return render_template(
            "restaurants.html",
            restaurants=restaurants
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN MENU
# =========================================================

@app.route("/admin/menu")
@admin_required
def menu_page():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                M.Item_ID,
                R.Restaurant_Name,
                M.Item_Name,
                M.Category,
                M.Price
            FROM MENU_ITEM M
            JOIN RESTAURANT R
                ON M.Restaurant_ID = R.Restaurant_ID
            ORDER BY M.Item_ID
            """
        )

        menu = cursor.fetchall()

        return render_template(
            "menu.html",
            menu=menu
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN ORDERS
# =========================================================

@app.route("/admin/orders")
@admin_required
def orders_page():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                O.Order_ID,
                C.Name,
                R.Restaurant_Name,
                O.Order_Date,
                O.Total_Amount,
                O.Order_Status
            FROM FOOD_ORDER O
            JOIN CUSTOMER C
                ON O.Customer_ID = C.Customer_ID
            JOIN RESTAURANT R
                ON O.Restaurant_ID = R.Restaurant_ID
            ORDER BY O.Order_ID
            """
        )

        orders = cursor.fetchall()

        return render_template(
            "orders.html",
            orders=orders
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN ORDER DETAILS
# =========================================================

@app.route("/admin/order_details/<int:order_id>")
@admin_required
def order_details_page(order_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                OD.Order_Detail_ID,
                OD.Order_ID,
                MI.Item_Name,
                OD.Quantity,
                OD.Subtotal
            FROM ORDER_DETAIL OD
            JOIN MENU_ITEM MI
                ON OD.Item_ID = MI.Item_ID
            WHERE OD.Order_ID = %s
            ORDER BY OD.Order_Detail_ID
        """, (order_id,))

        order_details = cursor.fetchall()

        return render_template(
            "order_details.html",
            order_details=order_details,
            order_id=order_id
        )

    finally:
        cursor.close()
        connection.close()


# =========================================================
# ADMIN PAYMENTS
# =========================================================

@app.route("/admin/payments", methods=["GET", "POST"])
@admin_required
def payments_page():

    connection = get_connection()
    cursor = connection.cursor()

    message = None
    error = None

    try:

        # -----------------------------------------
        # REFUND PAYMENT
        # -----------------------------------------
        if (
            request.method == "POST"
            and request.form.get("action") == "refund"
        ):

            payment_id = request.form.get("payment_id")

            if not payment_id:

                error = "Payment ID is required."

            else:

                # Check payment and related order status
                cursor.execute(
                    """
                    SELECT
                        P.Payment_ID,
                        P.Payment_Status,
                        O.Order_Status
                    FROM PAYMENT P
                    JOIN FOOD_ORDER O
                        ON P.Order_ID = O.Order_ID
                    WHERE P.Payment_ID = %s
                    """,
                    (payment_id,)
                )

                payment = cursor.fetchone()

                if payment is None:

                    error = "Payment ID not found."

                else:

                    current_payment_status = payment[1]
                    order_status = payment[2]

                    # Only cancelled orders can be refunded
                    if order_status != "Cancelled":

                        error = (
                            "Payment can only be refunded "
                            "when the order is cancelled."
                        )

                    # Prevent duplicate refund
                    elif current_payment_status == "Refunded":

                        error = "This payment has already been refunded."

                    elif current_payment_status != "Paid":

                        error = "Only paid payments can be refunded."

                    else:

                        cursor.execute(
                            """
                            UPDATE PAYMENT
                            SET Payment_Status = 'Refunded'
                            WHERE Payment_ID = %s
                            """,
                            (payment_id,)
                        )

                        connection.commit()

                        message = (
                            "Payment refunded successfully."
                        )

        # -----------------------------------------
        # FETCH PAYMENTS
        # -----------------------------------------
        cursor.execute(
            """
            SELECT
                P.Payment_ID,
                P.Order_ID,
                P.Payment_Date,
                P.Amount,
                P.Payment_Method,
                P.Payment_Status,
                O.Order_Status
            FROM PAYMENT P
            JOIN FOOD_ORDER O
                ON P.Order_ID = O.Order_ID
            ORDER BY P.Payment_ID
            """
        )

        payments = cursor.fetchall()

        return render_template(
            "payments.html",
            payments=payments,
            message=message,
            error=error
        )

    except Exception as error_message:

        connection.rollback()

        print(
            "PAYMENT ERROR:",
            error_message
        )

        return render_template(
            "payments.html",
            payments=[],
            message=None,
            error="Unable to process payment operation."
        )

    finally:

        cursor.close()
        connection.close()

# =========================================================
# ADMIN DELIVERY PARTNERS
# =========================================================

@app.route("/admin/delivery_partners")
@admin_required
def delivery_partners_page():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Partner_ID,
                Name,
                Phone,
                Vehicle_Number,
                Aadhaar_Number,
                Login_Username
            FROM DELIVERY_PARTNER
            ORDER BY Partner_ID
            """
        )

        delivery_partners = cursor.fetchall()

        return render_template(
            "delivery_partners.html",
            delivery_partners=delivery_partners
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN DELIVERY MANAGEMENT
# =========================================================

@app.route("/admin/deliveries", methods=["GET", "POST"])
@admin_required
def deliveries_page():

    connection = get_connection()
    cursor = connection.cursor()

    message = None
    error = None

    try:

        # -------------------------------------------------
        # ASSIGN DELIVERY
        # -------------------------------------------------

        if (
            request.method == "POST"
            and request.form.get("action") == "assign"
        ):

            order_id = request.form.get(
                "order_id"
            )

            partner_id = request.form.get(
                "partner_id"
            )

            cursor.execute(
                """
                SELECT Order_ID
                FROM FOOD_ORDER
                WHERE Order_ID = %s
                """,
                (order_id,)
            )

            order = cursor.fetchone()

            if order is None:

                error = "Order ID not found."

            else:

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM DELIVERY
                    WHERE Order_ID = %s
                    """,
                    (order_id,)
                )

                already_assigned = cursor.fetchone()[0]

                if already_assigned > 0:

                    error = (
                        "This order already has a delivery assigned."
                    )

                else:

                    cursor.execute(
                        """
                        SELECT Partner_ID
                        FROM DELIVERY_PARTNER
                        WHERE Partner_ID = %s
                        """,
                        (partner_id,)
                    )

                    partner = cursor.fetchone()

                    if partner is None:

                        error = "Delivery partner not found."

                    else:

                        delivery_id = get_next_id(
                            cursor,
                            "DELIVERY",
                            "Delivery_ID"
                        )

                        cursor.execute(
                            """
                            INSERT INTO DELIVERY
                            (
                                Delivery_ID,
                                Order_ID,
                                Partner_ID,
                                Delivery_Status
                            )
                            VALUES
                            (
                                %s,
                                %s,
                                %s,
                                'Assigned'
                            )
                            """,
                            (
                                delivery_id,
                                order_id,
                                partner_id
                            )
                        )

                        connection.commit()

                        message = (
                            "Delivery assigned successfully."
                        )

        # -------------------------------------------------
        # UPDATE DELIVERY
        # -------------------------------------------------

        elif (
            request.method == "POST"
            and request.form.get("action") == "update_status"
        ):

            delivery_id = request.form.get(
                "delivery_id"
            )

            delivery_status = request.form.get(
                "delivery_status"
            )

            valid_statuses = (
                "Assigned",
                "Picked Up",
                "Out for Delivery",
                "Delivered",
                "Cancelled"
            )

            if delivery_status not in valid_statuses:

                error = "Invalid delivery status."

            else:

                cursor.execute(
                    """
                    SELECT Order_ID
                    FROM DELIVERY
                    WHERE Delivery_ID = %s
                    """,
                    (delivery_id,)
                )

                delivery = cursor.fetchone()

                if delivery is None:

                    error = "Delivery ID not found."

                else:

                    order_id = delivery[0]

                    if delivery_status == "Delivered":

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET
                                Delivery_Status = %s,
                                Delivery_Date = CURRENT_TIMESTAMP
                            WHERE Delivery_ID = %s
                            """,
                            (
                                delivery_status,
                                delivery_id
                            )
                        )

                    else:

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET Delivery_Status = %s
                            WHERE Delivery_ID = %s
                            """,
                            (
                                delivery_status,
                                delivery_id
                            )
                        )

                    update_order_from_delivery(
                        cursor,
                        order_id,
                        delivery_status
                    )

                    connection.commit()

                    message = (
                        "Delivery and order status "
                        "updated successfully."
                    )

        # -------------------------------------------------
        # ORDERS WITHOUT DELIVERY
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                F.Order_ID,
                C.Name,
                F.Order_Status,
                F.Total_Amount
            FROM FOOD_ORDER F
            JOIN CUSTOMER C
                ON F.Customer_ID = C.Customer_ID
            WHERE NOT EXISTS
            (
                SELECT 1
                FROM DELIVERY D
                WHERE D.Order_ID = F.Order_ID
            )
            ORDER BY F.Order_ID
            """
        )

        pending_orders = cursor.fetchall()

        # -------------------------------------------------
        # DELIVERY PARTNERS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                Partner_ID,
                Name,
                Phone,
                Vehicle_Number
            FROM DELIVERY_PARTNER
            ORDER BY Partner_ID
            """
        )

        partners = cursor.fetchall()

        # -------------------------------------------------
        # ALL DELIVERIES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                D.Delivery_ID,
                D.Order_ID,
                DP.Name,
                D.Delivery_Date,
                D.Delivery_Status
            FROM DELIVERY D
            JOIN DELIVERY_PARTNER DP
                ON D.Partner_ID = DP.Partner_ID
            ORDER BY D.Delivery_ID
            """
        )

        deliveries = cursor.fetchall()

        return render_template(
            "deliveries.html",
            deliveries=deliveries,
            pending_orders=pending_orders,
            partners=partners,
            message=message,
            error=error
        )

    except Exception as error_message:

        connection.rollback()

        print(
            "DELIVERY ERROR:",
            error_message
        )

        return render_template(
            "deliveries.html",
            deliveries=[],
            pending_orders=[],
            partners=[],
            message=None,
            error="Unable to process delivery operation."
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# UPDATE ORDER STATUS FROM ADMIN
# =========================================================

@app.route(
    "/admin/update_order",
    methods=["GET", "POST"]
)
@admin_required
def update_order():

    message = None

    if request.method == "POST":

        order_id = request.form.get(
            "order_id"
        )

        status = request.form.get(
            "status"
        )

        valid_statuses = (
            "Placed",
            "Preparing",
            "Out for Delivery",
            "Delivered",
            "Cancelled"
        )

        if status not in valid_statuses:

            message = "Invalid order status."

        else:

            connection = get_connection()
            cursor = connection.cursor()

            try:

                cursor.execute(
                    """
                    SELECT Order_ID
                    FROM FOOD_ORDER
                    WHERE Order_ID = %s
                    """,
                    (order_id,)
                )

                order = cursor.fetchone()

                if order is None:

                    message = "Order ID not found."

                else:

                    cursor.execute(
                        """
                        UPDATE FOOD_ORDER
                        SET Order_Status = %s
                        WHERE Order_ID = %s
                        """,
                        (
                            status,
                            order_id
                        )
                    )

                    if status in (
                        "Placed",
                        "Preparing"
                    ):

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET Delivery_Status = 'Assigned'
                            WHERE Order_ID = %s
                            """,
                            (order_id,)
                        )

                    elif status == "Out for Delivery":

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET Delivery_Status = 'Out for Delivery'
                            WHERE Order_ID = %s
                            """,
                            (order_id,)
                        )

                    elif status == "Delivered":

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET
                                Delivery_Status = 'Delivered',
                                Delivery_Date = CURRENT_TIMESTAMP
                            WHERE Order_ID = %s
                            """,
                            (order_id,)
                        )

                    elif status == "Cancelled":

                        cursor.execute(
                            """
                            UPDATE DELIVERY
                            SET Delivery_Status = 'Cancelled'
                            WHERE Order_ID = %s
                            """,
                            (order_id,)
                        )

                    connection.commit()

                    message = (
                        "Order and delivery status "
                        "updated successfully."
                    )

            except Exception as error:

                connection.rollback()

                print(
                    "UPDATE ORDER ERROR:",
                    error
                )

                message = (
                    "Unable to update order status."
                )

            finally:

                cursor.close()
                connection.close()

    return render_template(
        "update_order.html",
        message=message
    )


# =========================================================
# CUSTOMER PORTAL
# =========================================================

@app.route("/customer")
@customer_required
def customer_home():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Restaurant_ID,
                Restaurant_Name,
                Location,
                Phone
            FROM RESTAURANT
            ORDER BY Restaurant_ID
            """
        )

        restaurants = cursor.fetchall()

        return render_template(
            "customer_home.html",
            restaurants=restaurants
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# CUSTOMER MENU
# =========================================================

@app.route("/customer/menu/<int:restaurant_id>")
@customer_required
def customer_menu(restaurant_id):

    customer_id = session.get("customer_id")

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                Customer_ID,
                Name,
                Phone,
                Email,
                Address
            FROM CUSTOMER
            WHERE Customer_ID = %s
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            session.clear()
            return redirect(url_for("login"))

        cursor.execute(
            """
            SELECT
                Restaurant_ID,
                Restaurant_Name,
                Location,
                Phone
            FROM RESTAURANT
            WHERE Restaurant_ID = %s
            """,
            (restaurant_id,)
        )

        restaurant = cursor.fetchone()

        if restaurant is None:
            return render_template(
                "order_error.html",
                message="Restaurant not found."
            )

        cursor.execute(
            """
            SELECT
                Item_ID,
                Restaurant_ID,
                Item_Name,
                Category,
                Price
            FROM MENU_ITEM
            WHERE Restaurant_ID = %s
            ORDER BY Item_ID
            """,
            (restaurant_id,)
        )

        menu_items = cursor.fetchall()

        return render_template(
            "place_order.html",
            customer=customer,
            restaurant=restaurant,
            menu_items=menu_items
        )

    finally:
        cursor.close()
        connection.close()


@app.route("/customer/orders")
@customer_required
def customer_orders():

    customer_id = session.get("customer_id")

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Get all orders placed by the logged-in customer
        cursor.execute(
            """
            SELECT
                O.Order_ID,
                O.Order_Date,
                R.Restaurant_Name,
                O.Total_Amount,
                O.Order_Status
            FROM FOOD_ORDER O
            JOIN RESTAURANT R
                ON O.Restaurant_ID = R.Restaurant_ID
            WHERE O.Customer_ID = %s
            ORDER BY O.Order_ID DESC
            """,
            (customer_id,)
        )

        orders = cursor.fetchall()

        # Get all order details
        order_details = {}

        for order in orders:

            order_id = order[0]

            cursor.execute(
                """
                SELECT
                    OD.Item_ID,
                    MI.Item_Name,
                    MI.Category,
                    OD.Quantity,
                    OD.Subtotal
                FROM ORDER_DETAIL OD
                JOIN MENU_ITEM MI
                    ON OD.Item_ID = MI.Item_ID
                WHERE OD.Order_ID = %s
                ORDER BY OD.Order_Detail_ID
                """,
                (order_id,)
            )

            order_details[order_id] = cursor.fetchall()

        return render_template(
            "customer_orders.html",
            orders=orders,
            order_details=order_details
        )

    finally:
        cursor.close()
        connection.close()


@app.route("/customer/cancel_order/<int:order_id>", methods=["POST"])
@customer_required
def cancel_customer_order(order_id):

    customer_id = session.get("customer_id")

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # Make sure this order belongs to the logged-in customer
        cursor.execute(
            """
            SELECT
                Order_Status
            FROM FOOD_ORDER
            WHERE Order_ID = %s
              AND Customer_ID = %s
            """,
            (order_id, customer_id)
        )

        order = cursor.fetchone()

        if order is None:

            return redirect(
                url_for("customer_orders")
            )

        current_status = order[0]

        # Customer can cancel only Placed or Preparing orders
        if current_status not in ["Placed", "Preparing"]:

            return redirect(
                url_for("customer_orders")
            )

        # Cancel the order
        cursor.execute(
            """
            UPDATE FOOD_ORDER
            SET Order_Status = 'Cancelled'
            WHERE Order_ID = %s
              AND Customer_ID = %s
            """,
            (order_id, customer_id)
        )

        # If there is a delivery record, cancel it too
        cursor.execute(
            """
            UPDATE DELIVERY
            SET Delivery_Status = 'Cancelled'
            WHERE Order_ID = %s
              AND Partner_ID IS NOT NULL
            """,
            (order_id,)
        )

        connection.commit()

        return redirect(
            url_for("customer_orders")
        )

    except Exception as error_message:

        connection.rollback()

        print(
            "CUSTOMER ORDER CANCELLATION ERROR:",
            error_message
        )

        return redirect(
            url_for("customer_orders")
        )

    finally:

        cursor.close()
        connection.close()

# =========================================================
# CUSTOMER PLACE ORDER
# =========================================================

@app.route(
    "/customer/place_order/<int:restaurant_id>",
    methods=["POST"]
)
@customer_required
def place_order(restaurant_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        customer_id = session.get("customer_id")

        payment_method = request.form.get(
            "payment_method"
        )

        # -------------------------------------------------
        # CHECK PAYMENT METHOD
        # -------------------------------------------------

        valid_payment_methods = [
            "Cash",
            "UPI",
            "Card",
            "Net Banking"
        ]

        if payment_method not in valid_payment_methods:

            return render_template(
                "order_error.html",
                message="Please select a valid payment method."
            )

        # -------------------------------------------------
        # DETERMINE INITIAL PAYMENT STATUS
        # -------------------------------------------------

        if payment_method == "Cash":

            payment_status = "Pending"

        else:

            # UPI, Card and Net Banking
            # are treated as paid before delivery.
            payment_status = "Paid"

        # -------------------------------------------------
        # CHECK CUSTOMER
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT Customer_ID
            FROM CUSTOMER
            WHERE Customer_ID = %s
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:

            session.clear()

            return redirect(
                url_for("login")
            )

        # -------------------------------------------------
        # CHECK RESTAURANT
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT Restaurant_ID
            FROM RESTAURANT
            WHERE Restaurant_ID = %s
            """,
            (restaurant_id,)
        )

        if cursor.fetchone() is None:

            return "Restaurant not found", 404

        # -------------------------------------------------
        # COLLECT ITEMS
        # -------------------------------------------------

        selected_items = []
        total_amount = 0

        for field_name in request.form:

            if not field_name.startswith(
                "quantity_"
            ):
                continue

            try:

                item_id = int(
                    field_name.replace(
                        "quantity_",
                        ""
                    )
                )

                quantity = int(
                    request.form[field_name]
                )

            except ValueError:

                continue

            if quantity <= 0:

                continue

            cursor.execute(
                """
                SELECT
                    Item_ID,
                    Price
                FROM MENU_ITEM
                WHERE Item_ID = %s
                  AND Restaurant_ID = %s
                """,
                (
                    item_id,
                    restaurant_id
                )
            )

            item = cursor.fetchone()

            if item is None:

                continue

            price = float(item[1])

            subtotal = price * quantity

            selected_items.append(
                (
                    item_id,
                    quantity,
                    subtotal
                )
            )

            total_amount += subtotal

        # -------------------------------------------------
        # CHECK ITEMS
        # -------------------------------------------------

        if not selected_items:

            connection.rollback()

            return render_template(
                "order_error.html",
                message=(
                    "Please select at least one "
                    "food item."
                )
            )

        # -------------------------------------------------
        # CREATE ORDER
        # -------------------------------------------------

        order_id = get_next_id(
            cursor,
            "FOOD_ORDER",
            "Order_ID"
        )

        cursor.execute(
            """
            INSERT INTO FOOD_ORDER
            (
                Order_ID,
                Customer_ID,
                Restaurant_ID,
                Total_Amount,
                Order_Status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Placed'
            )
            """,
            (
                order_id,
                customer_id,
                restaurant_id,
                total_amount
            )
        )

        # -------------------------------------------------
        # ORDER DETAILS
        # -------------------------------------------------

        for (
            item_id,
            quantity,
            subtotal
        ) in selected_items:

            order_detail_id = get_next_id(
                cursor,
                "ORDER_DETAIL",
                "Order_Detail_ID"
            )

            cursor.execute(
                """
                INSERT INTO ORDER_DETAIL
                (
                    Order_Detail_ID,
                    Order_ID,
                    Item_ID,
                    Quantity,
                    Subtotal
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    order_detail_id,
                    order_id,
                    item_id,
                    quantity,
                    subtotal
                )
            )

        # -------------------------------------------------
        # PAYMENT
        # -------------------------------------------------

        payment_id = get_next_id(
            cursor,
            "PAYMENT",
            "Payment_ID"
        )

        cursor.execute(
            """
            INSERT INTO PAYMENT
            (
                Payment_ID,
                Order_ID,
                Amount,
                Payment_Method,
                Payment_Status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                payment_id,
                order_id,
                total_amount,
                payment_method,
                payment_status
            )
        )

        connection.commit()

        return redirect(
            url_for(
                "order_success",
                order_id=order_id
            )
        )

    except Exception as error:

        connection.rollback()

        print(
            "CUSTOMER ORDER ERROR:",
            error
        )

        return render_template(
            "order_error.html",
            message=(
                "Unable to place the order. "
                "Please try again."
            )
        )

    finally:

        cursor.close()
        connection.close()

# =========================================================
# CUSTOMER ORDER SUCCESS
# =========================================================

@app.route(
    "/customer/order_success/<int:order_id>"
)
@customer_required
def order_success(order_id):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        customer_id = session.get(
            "customer_id"
        )

        cursor.execute(
            """
            SELECT
                O.Order_ID,
                C.Name,
                R.Restaurant_Name,
                O.Total_Amount,
                O.Order_Status
            FROM FOOD_ORDER O
            JOIN CUSTOMER C
                ON O.Customer_ID = C.Customer_ID
            JOIN RESTAURANT R
                ON O.Restaurant_ID = R.Restaurant_ID
            WHERE O.Order_ID = %s
              AND O.Customer_ID = %s
            """,
            (
                order_id,
                customer_id
            )
        )

        order = cursor.fetchone()

        if order is None:

            return "Order not found", 404

        return render_template(
            "order_success.html",
            order=order
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# DELIVERY PARTNER DASHBOARD
# =========================================================
@app.route("/delivery/dashboard", methods=["GET", "POST"])
@delivery_required
def delivery_dashboard():

    partner_id = session.get("partner_id")

    connection = get_connection()
    cursor = connection.cursor()

    message = None
    error = None
    partner = None

    try:

        # =====================================================
        # PARTNER DETAILS
        # =====================================================

        cursor.execute(
            """
            SELECT
                Partner_ID,
                Name,
                Phone,
                Vehicle_Number,
                Aadhaar_Number,
                Login_Username
            FROM DELIVERY_PARTNER
            WHERE Partner_ID = %s
            """,
            (partner_id,)
        )

        partner = cursor.fetchone()

        if partner is None:
            session.clear()
            return redirect(url_for("login"))

        # =====================================================
        # UPDATE DELIVERY STATUS
        # =====================================================

        if request.method == "POST":

            delivery_id = request.form.get("delivery_id")
            requested_status = request.form.get("delivery_status")

            valid_statuses = (
                "Assigned",
                "Picked Up",
                "Out for Delivery",
                "Delivered",
                "Cancelled"
            )

            if requested_status not in valid_statuses:

                error = "Invalid delivery status."

            else:

                cursor.execute(
                    """
                    SELECT
                        D.Delivery_ID,
                        D.Order_ID,
                        D.Delivery_Status,
                        O.Order_Status
                    FROM DELIVERY D
                    JOIN FOOD_ORDER O
                        ON D.Order_ID = O.Order_ID
                    WHERE D.Delivery_ID = %s
                      AND D.Partner_ID = %s
                    """,
                    (delivery_id, partner_id)
                )

                delivery = cursor.fetchone()

                if delivery is None:

                    error = (
                        "This delivery is not assigned to you."
                    )

                else:

                    current_delivery_status = delivery[2]
                    order_id = delivery[1]

                    # -----------------------------------------
                    # ALLOWED DELIVERY STATUS TRANSITIONS
                    # -----------------------------------------

                    allowed_next_statuses = {
                        "Assigned": ["Picked Up"],
                        "Picked Up": ["Out for Delivery"],
                        "Out for Delivery": [
                            "Delivered",
                            "Cancelled"
                        ],
                        "Delivered": [],
                        "Cancelled": []
                    }

                    allowed_statuses = allowed_next_statuses.get(
                        current_delivery_status,
                        []
                    )

                    if requested_status not in allowed_statuses:

                        error = (
                            "Invalid status transition. "
                            f"Current status is "
                            f"'{current_delivery_status}'."
                        )

                    else:

                        # =====================================
                        # PICKED UP
                        # =====================================

                        if requested_status == "Picked Up":

                            cursor.execute(
                                """
                                UPDATE DELIVERY
                                SET Delivery_Status = 'Picked Up'
                                WHERE Delivery_ID = %s
                                  AND Partner_ID = %s
                                """,
                                (delivery_id, partner_id)
                            )

                            # FOOD_ORDER remains unchanged.
                            # It should NOT become "Picked Up".

                        # =====================================
                        # OUT FOR DELIVERY
                        # =====================================

                        elif requested_status == "Out for Delivery":

                            cursor.execute(
                                """
                                UPDATE DELIVERY
                                SET Delivery_Status = 'Out for Delivery'
                                WHERE Delivery_ID = %s
                                  AND Partner_ID = %s
                                """,
                                (delivery_id, partner_id)
                            )

                            cursor.execute(
                                """
                                UPDATE FOOD_ORDER
                                SET Order_Status = 'Out for Delivery'
                                WHERE Order_ID = %s
                                """,
                                (order_id,)
                            )

                        # =====================================
                        # DELIVERED
                        # =====================================

                        elif requested_status == "Delivered":

                            cursor.execute(
                                """
                                UPDATE DELIVERY
                                SET
                                    Delivery_Status = 'Delivered',
                                    Delivery_Date = CURRENT_TIMESTAMP
                                WHERE Delivery_ID = %s
                                  AND Partner_ID = %s
                                """,
                                (delivery_id, partner_id)
                            )

                            cursor.execute(
                                """
                                UPDATE FOOD_ORDER
                                SET Order_Status = 'Delivered'
                                WHERE Order_ID = %s
                                """,
                                (order_id,)
                            )

                            # ---------------------------------
                            # CHECK PAYMENT
                            # ---------------------------------

                            cursor.execute(
                                """
                                SELECT
                                    Payment_ID,
                                    Payment_Method,
                                    Payment_Status
                                FROM PAYMENT
                                WHERE Order_ID = %s
                                """,
                                (order_id,)
                            )

                            payment = cursor.fetchone()

                            if payment is not None:

                                payment_id = payment[0]
                                payment_method = payment[1]
                                payment_status = payment[2]

                                # COD:
                                # Cash + Pending -> Paid

                                if (
                                    payment_method == "Cash"
                                    and payment_status == "Pending"
                                ):

                                    cursor.execute(
                                        """
                                        UPDATE PAYMENT
                                        SET Payment_Status = 'Paid'
                                        WHERE Payment_ID = %s
                                        """,
                                        (payment_id,)
                                    )

                        # =====================================
                        # CANCELLED
                        # =====================================

                        elif requested_status == "Cancelled":

                            cursor.execute(
                                """
                                UPDATE DELIVERY
                                SET Delivery_Status = 'Cancelled'
                                WHERE Delivery_ID = %s
                                  AND Partner_ID = %s
                                """,
                                (delivery_id, partner_id)
                            )

                            cursor.execute(
                                """
                                UPDATE FOOD_ORDER
                                SET Order_Status = 'Cancelled'
                                WHERE Order_ID = %s
                                """,
                                (order_id,)
                            )

                            # Payment status intentionally
                            # remains unchanged.

                        connection.commit()

                        message = (
                            "Delivery status updated successfully."
                        )

        # =====================================================
        # GET PARTNER DELIVERIES
        # =====================================================

        cursor.execute(
            """
            SELECT
                D.Delivery_ID,
                D.Order_ID,

                C.Name,
                C.Phone,
                C.Address,

                R.Restaurant_Name,
                R.Location,

                O.Total_Amount,
                O.Order_Status,

                D.Delivery_Date,
                D.Delivery_Status

            FROM DELIVERY D

            JOIN FOOD_ORDER O
                ON D.Order_ID = O.Order_ID

            JOIN CUSTOMER C
                ON O.Customer_ID = C.Customer_ID

            JOIN RESTAURANT R
                ON O.Restaurant_ID = R.Restaurant_ID

            WHERE D.Partner_ID = %s

            ORDER BY D.Delivery_ID DESC
            """,
            (partner_id,)
        )

        deliveries = cursor.fetchall()

        return render_template(
            "delivery/dashboard.html",
            partner=partner,
            deliveries=deliveries,
            message=message,
            error=error
        )

    except Exception as error_message:

        connection.rollback()

        print(
            "DELIVERY GUY ERROR:",
            error_message
        )

        return render_template(
            "delivery/dashboard.html",
            partner=partner,
            deliveries=[],
            message=None,
            error="Unable to process delivery operation."
        )

    finally:

        cursor.close()
        connection.close()


# =========================================================
# SYNCHRONIZE DELIVERY → FOOD ORDER
# =========================================================

def update_order_from_delivery(
    cursor,
    order_id,
    delivery_status
):

    if delivery_status == "Assigned":

        order_status = "Preparing"

    elif delivery_status == "Picked Up":

        order_status = "Out for Delivery"

    elif delivery_status == "Out for Delivery":

        order_status = "Out for Delivery"

    elif delivery_status == "Delivered":

        order_status = "Delivered"

    elif delivery_status == "Cancelled":

        order_status = "Cancelled"

    else:

        order_status = "Placed"

    cursor.execute(
        """
        UPDATE FOOD_ORDER
        SET Order_Status = %s
        WHERE Order_ID = %s
        """,
        (
            order_status,
            order_id
        )
    )


# =========================================================
# ROOT REDIRECT
# =========================================================

@app.route("/")
def root():

    role = session.get("role")

    if role == "admin":

        return redirect(
            url_for("admin_dashboard")
        )

    if role == "customer":

        return redirect(
            url_for("customer_home")
        )

    if role == "delivery":

        return redirect(
            url_for("delivery_dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)