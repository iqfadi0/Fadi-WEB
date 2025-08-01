from flask import Flask, request, jsonify, render_template_string, Response
import json
import os
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

app = Flask(__name__)

DATA_FILE = "customers.json"

USERNAME = os.getenv("BASIC_AUTH_USERNAME", "admin")
PASSWORD = os.getenv("BASIC_AUTH_PASSWORD", "1234")

TELEGRAM_TOKEN = "8003548627:AAHpSyXnVK-Nyz-oCzPUddcXQ9PQQPSAeQo"  # Bot token
CHAT_ID = 7777263915  # Your Telegram chat ID

bot = Bot(token=TELEGRAM_TOKEN)

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.before_request
def require_auth():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

def load_customers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_customers(customers):
    with open(DATA_FILE, "w") as f:
        json.dump(customers, f, indent=2)

@app.route("/")
def index():
    customers = load_customers()
    return render_template_string(HTML_TEMPLATE, customers=customers)

@app.route("/add_customer", methods=["POST"])
def add_customer():
    data = request.json
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    app_name = data.get("app_name", "").strip()

    if not name or not phone or not app_name:
        return jsonify({"success": False, "message": "Missing fields."})

    customers = load_customers()

    if any(c["phone"] == phone for c in customers):
        return jsonify({"success": False, "message": "Customer with this phone already exists."})

    join_date = datetime.now()
    end_date = join_date + timedelta(days=30)  # إضافة شهر واحد لتاريخ الانتهاء

    new_customer = {
        "name": name,
        "phone": phone,
        "app_name": app_name,
        "join_date": join_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "paid": False
    }
    customers.append(new_customer)
    save_customers(customers)
    return jsonify({"success": True})

@app.route("/delete_customer", methods=["POST"])
def delete_customer():
    data = request.json
    phone = data.get("phone", "").strip()
    customers = load_customers()
    new_list = [c for c in customers if c["phone"] != phone]
    if len(new_list) == len(customers):
        return jsonify({"success": False, "message": "Customer not found."})
    save_customers(new_list)
    return jsonify({"success": True})

@app.route("/mark_paid", methods=["POST"])
def mark_paid():
    data = request.json
    phone = data.get("phone", "").strip()
    customers = load_customers()
    found = False
    for c in customers:
        if c["phone"] == phone:
            c["paid"] = True
            found = True
            break
    if not found:
        return jsonify({"success": False, "message": "Customer not found."})
    save_customers(customers)
    return jsonify({"success": True})

def send_telegram_reminder():
    try:
        message = "Daily reminder: Don't forget to review the customer list and update statuses."
        bot.send_message(chat_id=CHAT_ID, text=message)
        print("Telegram reminder sent.")
    except Exception as e:
        print("Error sending Telegram message:", e)

scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Beirut"))
scheduler.add_job(send_telegram_reminder, 'cron', hour=10, minute=0)
scheduler.start()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Customer Management System</title>
<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  body {
    background-color: #121212;
    color: #eee;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
    padding: 30px 15px;
  }
  header {
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 25px;
    color: #00d8ff;
    text-shadow: 0 0 8px #00d8ff99;
    text-align: center;
  }
  main {
    background-color: #1e1e1e;
    border-radius: 12px;
    max-width: 600px;
    margin: 0 auto;
    box-shadow: 0 0 15px #00d8ff44;
    padding: 20px 25px;
  }
  h2 {
    color: #00d8ff;
    margin-bottom: 15px;
    font-weight: 600;
    border-bottom: 2px solid #00d8ff;
    padding-bottom: 8px;
  }
  form {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  input[type="text"] {
    flex: 1 1 25%;
    padding: 10px;
    border-radius: 6px;
    border: none;
    font-size: 1rem;
  }
  button {
    background-color: #00aaff;
    color: #121212;
    border: none;
    padding: 12px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 1rem;
    transition: background-color 0.3s ease;
    flex: 1 1 15%;
    min-width: 120px;
  }
  button:hover {
    background-color: #008fcc;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 0.9rem;
  }
  th, td {
    padding: 10px;
    border-bottom: 1px solid #333;
    text-align: left;
    word-break: break-word;
  }
  th {
    background-color: #00d8ff;
    color: #121212;
  }
  .paid {
    color: #4CAF50;
    font-weight: bold;
  }
  .not-paid {
    color: #ff5555;
    font-weight: bold;
  }
  .action-btn {
    background-color: #555;
    color: #eee;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    margin-right: 5px;
    font-size: 0.9rem;
    white-space: nowrap;
  }
  .action-btn:hover {
    background-color: #00aaff;
    color: #121212;
  }
  #message {
    margin-bottom: 15px;
    font-weight: 600;
    height: 24px;
    text-align: center;
  }
  @media (max-width: 480px) {
    body {
      padding: 20px 10px;
    }
    main {
      padding: 15px 15px;
      max-width: 100%;
      border-radius: 8px;
      box-shadow: none;
    }
    header {
      font-size: 1.5rem;
      margin-bottom: 20px;
    }
    form {
      flex-direction: column;
      gap: 12px;
    }
    input[type="text"], button {
      flex: 1 1 100%;
      min-width: unset;
      font-size: 1.1rem;
      padding: 12px;
    }
    button {
      min-width: unset;
    }
    table, thead, tbody, th, td, tr {
      display: block;
      width: 100%;
    }
    thead tr {
      display: none;
    }
    tbody tr {
      margin-bottom: 15px;
      background-color: #2a2a2a;
      border-radius: 8px;
      padding: 12px;
    }
    tbody td {
      padding: 6px 10px;
      position: relative;
      padding-left: 50%;
      text-align: right;
    }
    tbody td::before {
      position: absolute;
      left: 15px;
      top: 50%;
      transform: translateY(-50%);
      white-space: nowrap;
      font-weight: 600;
      color: #00d8ff;
      content: attr(data-label);
      text-align: left;
      font-size: 0.9rem;
    }
    .action-btn {
      font-size: 1rem;
      padding: 10px 16px;
      margin: 5px 5px 0 0;
      white-space: normal;
      display: inline-block;
      width: auto;
    }
  }
</style>
</head>
<body>
<header>Customer Management System</header>
<main>
  <h2>Add New Customer</h2>
  <div id="message"></div>
  <form id="addCustomerForm">
    <input type="text" id="name" placeholder="Name" required />
    <input type="text" id="phone" placeholder="Phone Number" required />
    <input type="text" id="app_name" placeholder="App Name" required />
    <button type="submit">Add Customer</button>
  </form>

  <h2 style="display: flex; align-items: center; justify-content: space-between; cursor: pointer;" id="toggleCustomersHeader">
    Customers List
    <span id="toggleArrow" style="font-size: 1.3rem; user-select: none;">▼</span>
  </h2>
  <table id="customersTable">
    <thead>
      <tr>
        <th>Name</th>
        <th>Phone</th>
        <th>App Name</th>
        <th>Join Date</th>
        <th>End Date</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for customer in customers %}
      <tr>
        <td data-label="Name">{{ customer.name }}</td>
        <td data-label="Phone">{{ customer.phone }}</td>
        <td data-label="App Name">{{ customer.app_name }}</td>
        <td data-label="Join Date">{{ customer.join_date }}</td>
        <td data-label="End Date">{{ customer.end_date }}</td>
        <td data-label="Status">
          {% if customer.paid %}
            <span class="paid">Paid</span>
          {% else %}
            <span class="not-paid">Not Paid</span>
          {% endif %}
        </td>
        <td data-label="Actions">
          {% if not customer.paid %}
          <button class="action-btn mark-paid-btn" data-phone="{{ customer.phone }}">Mark Paid</button>
          {% endif %}
          <button class="action-btn delete-btn" data-phone="{{ customer.phone }}">Delete</button>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</main>

<script>
  const form = document.getElementById("addCustomerForm");
  const messageDiv = document.getElementById("message");
  const customersTableBody = document.getElementById("customersTable").getElementsByTagName('tbody')[0];

  function showMessage(text, isError = false) {
    messageDiv.textContent = text;
    messageDiv.style.color = isError ? "red" : "#00d8ff";
    setTimeout(() => {
      messageDiv.textContent = "";
    }, 3000);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const app_name = document.getElementById("app_name").value.trim();

    if (!name || !phone || !app_name) {
      showMessage("Please enter name, phone, and app name.", true);
      return;
    }

    try {
      const response = await fetch("/add_customer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone, app_name }),
      });
      const data = await response.json();
      if (data.success) {
        location.reload();
      } else {
        showMessage(data.message, true);
      }
    } catch (err) {
      showMessage("Error adding customer.", true);
    }
  });

  customersTableBody.addEventListener("click", async (e) => {
    if (e.target.classList.contains("delete-btn")) {
      const phone = e.target.getAttribute("data-phone");
      if (!confirm("Are you sure you want to delete this customer?")) return;

      try {
        const response = await fetch("/delete_customer", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone }),
        });
        const data = await response.json();
        if (data.success) {
          location.reload();
        } else {
          showMessage(data.message, true);
        }
      } catch {
        showMessage("Error deleting customer.", true);
      }
    }

    if (e.target.classList.contains("mark-paid-btn")) {
      const phone = e.target.getAttribute("data-phone");
      try {
        const response = await fetch("/mark_paid", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone }),
        });
        const data = await response.json();
        if (data.success) {
          location.reload();
        } else {
          showMessage(data.message, true);
        }
      } catch {
        showMessage("Error marking paid.", true);
      }
    }
  });

  const toggleHeader = document.getElementById("toggleCustomersHeader");
  const customersTable = document.getElementById("customersTable");
  const toggleArrow = document.getElementById("toggleArrow");
  let isTableVisible = true;

  toggleHeader.addEventListener("click", () => {
    if (isTableVisible) {
      customersTable.style.display = "none";
      toggleArrow.textContent = "▲";
    } else {
      customersTable.style.display = "table";
      toggleArrow.textContent = "▼";
    }
    isTableVisible = !isTableVisible;
  });
</script>
</body>
</html>
'''

if __name__ == "__main__":
    app.run(debug=True)
