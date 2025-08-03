import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import requests

# Function to fetch exchange rates from API
def get_exchange_rates():
    try:
        api_key = "VvVzYCurdo2MzlZIVR1LZYXQeb8IWRmZ"
        url = "https://api.apilayer.com/exchangerates_data/latest?base=USD"
        headers = {"apikey": api_key}
        response = requests.get(url, headers=headers)  
        data = response.json()
        return data.get("rates", {})
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch exchange rates: {e}")
        return {"USD": 1.0, "EUR": 1.1, "GBP": 1.3}  # Default values in case of request failure

# Function to convert amount to USD
def convert_to_usd(amount, currency, rates):
    return round(amount / rates.get(currency, 1), 2)

# Function to validate input fields
def validate_inputs():
    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return amount
    
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid amount.")
        return None

# Function to add a new expense
def add_expense():
    amount = validate_inputs()
    
    if amount is None:
        return
    
    currency = currency_var.get()
    category = category_var.get()
    payment_method = payment_var.get()
    date = date_entry.get()
    
    rates = get_exchange_rates()
    converted_amount = convert_to_usd(amount, currency, rates)
    expenses.append((amount, currency, category, payment_method, date, converted_amount))
    update_table()

# Function to update the table after adding expenses
def update_table():
    for row in tree.get_children():
        tree.delete(row)
    total_usd = sum(expense[5] for expense in expenses)
    
    for expense in expenses:
        tree.insert("", "end", values=expense[:5])
    
    tree.insert("", "end", values=(f"{total_usd:.2f}", "USD", "", "", ""), tags=("total",))
    tree.tag_configure("total", background="yellow", font=("Arial", 10, "bold"))

# Create application window
root = tk.Tk()
root.title("Expense Tracker")

expenses = []

# Input fields
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Amount").grid(row=0, column=0)
amount_entry = tk.Entry(frame)
amount_entry.grid(row=0, column=1)

tk.Label(frame, text="Currency").grid(row=1, column=0)
currency_var = ttk.Combobox(frame, values=["USD", "EUR", "GBP"], state="readonly")
currency_var.grid(row=1, column=1)
currency_var.current(0)

tk.Label(frame, text="Category").grid(row=2, column=0)
category_var = ttk.Combobox(frame, values=["Life", "Electricity", "Gas", "Rental", "Grocery", "Savings", "Education", "Charity"], state="readonly")
category_var.grid(row=2, column=1)
category_var.current(0)

tk.Label(frame, text="Payment Method").grid(row=3, column=0)
payment_var = ttk.Combobox(frame, values=["Cash", "Credit Card", "Paypal"], state="readonly")
payment_var.grid(row=3, column=1)
payment_var.current(0)

tk.Label(frame, text="Date").grid(row=4, column=0)
date_entry = tk.Entry(frame)
date_entry.grid(row=4, column=1)
date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))

add_button = tk.Button(frame, text="Add Expense", command=add_expense)
add_button.grid(row=5, column=1, pady=5)

# Create table
columns = ("Amount", "Currency", "Category", "Payment Method", "Date")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.pack(fill=tk.BOTH, expand=True)

root.mainloop()
