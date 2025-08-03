import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import requests

API_KEY = "VvVzYCurdo2MzlZIVR1LZYXQeb8IWRmZ"
API_URL = "https://api.apilayer.com/exchangerates_data/latest?base=USD"

# Fetch exchange rates
def get_exchange_rates():
    try:
        response = requests.get(API_URL, headers={"apikey": API_KEY})
        response.raise_for_status()
        return response.json().get("rates", {})
    except requests.RequestException:
        return {"USD": 1.0, "EUR": 1.1, "GBP": 1.3}  # Fallback rates

# Convert amount to USD
def convert_to_usd(amount, currency, rates):
    return round(amount / rates.get(currency, 1), 2)

# Validate amount input
def validate_amount():
    try:
        amount = float(amount_entry.get())
        if amount <= 0:
            raise ValueError
        return amount
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid amount.")
        return None

# Add expense to list and update UI
def add_expense():
    amount = validate_amount()
    if amount is None:
        return
    
    expense = (
        amount,
        currency_var.get(),
        category_var.get(),
        payment_var.get(),
        date_entry.get(),
        convert_to_usd(amount, currency_var.get(), rates)
    )
    expenses.append(expense)
    update_table()

# Update table with expenses
def update_table():
    tree.delete(*tree.get_children())
    total_usd = sum(exp[5] for exp in expenses)
    for exp in expenses:
        tree.insert("", "end", values=exp[:5])
    tree.insert("", "end", values=(f"{total_usd:.2f}", "USD", "", "", ""), tags=("total",))
    tree.tag_configure("total", background="#FFD700", font=("Arial", 10, "bold"))

# Initialize UI
root = tk.Tk()
root.title("Expense Tracker")
root.configure(bg="#f0f0f0")

expenses, rates = [], get_exchange_rates()

frame = tk.Frame(root, bg="#dfe6e9", padx=10, pady=10)
frame.pack(pady=10)

label_color = "#000000"  # Black text for labels
labels = ["Amount", "Currency", "Category", "Payment Method", "Date"]

for i, lbl in enumerate(labels):
    tk.Label(frame, text=lbl, font=("Arial", 12, "bold"), fg=label_color, padx=5, pady=5).grid(row=i, column=0, pady=5, sticky="w")

amount_entry = tk.Entry(frame, font=("Arial", 12))
amount_entry.grid(row=0, column=1, pady=5)

currency_var = ttk.Combobox(frame, values=list(rates.keys()), state="readonly", font=("Arial", 12))
currency_var.grid(row=1, column=1, pady=5)
currency_var.current(0)

category_var = ttk.Combobox(frame, values=["Life", "Electricity", "Gas", "Rental", "Grocery", "Savings", "Education", "Charity"], state="readonly", font=("Arial", 12))
category_var.grid(row=2, column=1, pady=5)
category_var.current(0)

payment_var = ttk.Combobox(frame, values=["Cash", "Credit Card", "Paypal"], state="readonly", font=("Arial", 12))
payment_var.grid(row=3, column=1, pady=5)
payment_var.current(0)

date_entry = DateEntry(frame, date_pattern='yyyy-mm-dd', font=("Arial", 12))
date_entry.grid(row=4, column=1, pady=5)

tk.Button(frame, text="Add Expense", command=add_expense, font=("Arial", 12, "bold"), bg="#00b894", fg="white", padx=10, pady=5).grid(row=5, column=1, pady=10)

columns = ("Amount", "Currency", "Category", "Payment Method", "Date")
tree = ttk.Treeview(root, columns=columns, show="headings")

# Styling the table header
style = ttk.Style()
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#2980b9", foreground="black")

for col in columns:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

root.mainloop()
