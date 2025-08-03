import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import requests
import json
import os
import csv
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker Pro")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10))
        self.style.configure('Treeview', font=('Helvetica', 10), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', '#347083')])
        
        # Initialize variables
        self.expenses = []
        self.rates = {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}  # Default rates
        self.load_exchange_rates()
        self.load_expenses()
        
        # Create UI
        self.create_widgets()
        self.update_table()
        self.update_summary()
        
    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Input form
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Add New Expense", padding=(10, 5))
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Input fields
        fields = [
            ("Amount", "amount_entry", None),
            ("Currency", "currency_var", ["USD", "EUR", "GBP"]),
            ("Category", "category_var", ["Life", "Food", "Housing", "Transport", 
                                        "Utilities", "Healthcare", "Entertainment", 
                                        "Education", "Savings", "Other"]),
            ("Payment Method", "payment_var", ["Cash", "Credit Card", "Debit Card", 
                                             "Bank Transfer", "PayPal", "Other"]),
            ("Date", "date_entry", None),
            ("Description", "desc_entry", None)
        ]
        
        for i, (label, var_name, values) in enumerate(fields):
            ttk.Label(self.input_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            
            if values:
                setattr(self, var_name, ttk.Combobox(self.input_frame, values=values, state="readonly"))
                getattr(self, var_name).grid(row=i, column=1, sticky="ew", pady=2, padx=5)
                getattr(self, var_name).current(0)
            else:
                if label == "Date":
                    setattr(self, var_name, ttk.Entry(self.input_frame))
                    getattr(self, var_name).grid(row=i, column=1, sticky="ew", pady=2, padx=5)
                    getattr(self, var_name).insert(0, datetime.today().strftime('%Y-%m-%d'))
                elif label == "Amount":
                    setattr(self, var_name, ttk.Entry(self.input_frame, validate="key"))
                    getattr(self, var_name).grid(row=i, column=1, sticky="ew", pady=2, padx=5)
                    getattr(self, var_name).config(validatecommand=(self.root.register(self.validate_amount), '%P'))
                else:
                    setattr(self, var_name, ttk.Entry(self.input_frame))
                    getattr(self, var_name).grid(row=i, column=1, sticky="ew", pady=2, padx=5)
        
        # Buttons
        self.button_frame = ttk.Frame(self.input_frame)
        self.button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        
        ttk.Button(self.button_frame, text="Add Expense", command=self.add_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Clear", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        # Right panel - Summary and table
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Summary frame
        self.summary_frame = ttk.LabelFrame(self.right_frame, text="Summary", padding=(10, 5))
        self.summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.summary_labels = {}
        metrics = ["Total Expenses (USD)", "This Month", "Most Spent Category", "Top Payment Method"]
        
        for i, metric in enumerate(metrics):
            ttk.Label(self.summary_frame, text=metric).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.summary_labels[metric] = ttk.Label(self.summary_frame, text="", font=('Helvetica', 10, 'bold'))
            self.summary_labels[metric].grid(row=i, column=1, sticky="e", padx=5, pady=2)
        
        # Table frame
        self.table_frame = ttk.LabelFrame(self.right_frame, text="Expenses", padding=(10, 5))
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview with scrollbars
        self.tree_scroll_y = ttk.Scrollbar(self.table_frame)
        self.tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_scroll_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL)
        self.tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        columns = ("Amount", "Currency", "Category", "Payment", "Date", "Description", "USD Amount")
        self.tree = ttk.Treeview(
            self.table_frame, 
            columns=columns, 
            show="headings",
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            selectmode="extended"
        )
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER if col in ["Amount", "USD Amount"] else tk.W)
        
        self.tree.column("Description", width=150)
        self.tree.column("Date", width=90)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
        
        # Context menu
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="Edit", command=self.edit_expense)
        self.tree_menu.add_command(label="Delete", command=self.delete_expense)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Bottom panel - Charts and export
        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        
        # Chart frame
        self.chart_frame = ttk.LabelFrame(self.bottom_frame, text="Expense Analysis", padding=(10, 5))
        self.chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Export buttons
        self.export_frame = ttk.Frame(self.bottom_frame)
        self.export_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        ttk.Button(self.export_frame, text="Export to CSV", command=self.export_csv).pack(fill=tk.X, pady=2)
        ttk.Button(self.export_frame, text="Export to JSON", command=self.export_json).pack(fill=tk.X, pady=2)
        ttk.Button(self.export_frame, text="Generate Report", command=self.generate_report).pack(fill=tk.X, pady=2)
        ttk.Button(self.export_frame, text="Refresh Rates", command=self.load_exchange_rates).pack(fill=tk.X, pady=2)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        self.main_frame.rowconfigure(0, weight=3)
        self.main_frame.rowconfigure(1, weight=1)
        
    def validate_amount(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def load_exchange_rates(self):
        try:
            api_key = "VvVzYCurdo2MzlZIVR1LZYXQeb8IWRmZ"
            url = "https://api.apilayer.com/exchangerates_data/latest?base=USD"
            headers = {"apikey": api_key}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.rates = data.get("rates", self.rates)
            messagebox.showinfo("Success", "Exchange rates updated successfully")
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to fetch exchange rates: {e}\nUsing default rates.")
    
    def validate_inputs(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            
            date_str = self.date_entry.get()
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format.")
            
            return amount
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return None
    
    def convert_to_usd(self, amount, currency):
        rate = self.rates.get(currency, 1.0)
        return round(amount / rate, 2)
    
    def add_expense(self):
        amount = self.validate_inputs()
        if amount is None:
            return
        
        currency = self.currency_var.get()
        category = self.category_var.get()
        payment = self.payment_var.get()
        date = self.date_entry.get()
        description = self.desc_entry.get()
        
        usd_amount = self.convert_to_usd(amount, currency)
        expense = {
            "amount": amount,
            "currency": currency,
            "category": category,
            "payment": payment,
            "date": date,
            "description": description,
            "usd_amount": usd_amount
        }
        
        self.expenses.append(expense)
        self.update_table()
        self.update_summary()
        self.update_charts()
        self.clear_fields()
        self.save_expenses()
        
    def edit_expense(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        values = item['values']
        index = self.tree.index(selected[0])
        
        if index >= len(self.expenses):  # Don't edit the total row
            return
        
        # Open edit window
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Expense")
        edit_win.grab_set()
        
        # Create form
        fields = ["Amount", "Currency", "Category", "Payment Method", "Date", "Description"]
        
        for i, field in enumerate(fields):
            ttk.Label(edit_win, text=field).grid(row=i, column=0, padx=5, pady=2, sticky="w")
            
            if field == "Currency":
                var = ttk.Combobox(edit_win, values=["USD", "EUR", "GBP"], state="readonly")
                var.current(["USD", "EUR", "GBP"].index(values[1]))
            elif field == "Category":
                var = ttk.Combobox(edit_win, values=["Life", "Food", "Housing", "Transport", 
                                                    "Utilities", "Healthcare", "Entertainment", 
                                                    "Education", "Savings", "Other"], state="readonly")
                var.set(values[2])
            elif field == "Payment Method":
                var = ttk.Combobox(edit_win, values=["Cash", "Credit Card", "Debit Card", 
                                                   "Bank Transfer", "PayPal", "Other"], state="readonly")
                var.set(values[3])
            else:
                var = ttk.Entry(edit_win)
                var.insert(0, values[0] if field == "Amount" else 
                           values[4] if field == "Date" else 
                           values[5] if field == "Description" else "")
            
            var.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            setattr(self, f"edit_{field.lower().replace(' ', '_')}", var)
        
        # Save button
        ttk.Button(
            edit_win, 
            text="Save Changes",
            command=lambda: self.save_edited_expense(index, edit_win)
        ).grid(row=len(fields), column=0, columnspan=2, pady=10)
    
    def save_edited_expense(self, index, window):
        try:
            amount = float(self.edit_amount.get())
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
            
            date_str = self.edit_date.get()
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format.")
            
            currency = self.edit_currency.get()
            category = self.edit_category.get()
            payment = self.edit_payment_method.get()
            description = self.edit_description.get()
            
            usd_amount = self.convert_to_usd(amount, currency)
            
            self.expenses[index] = {
                "amount": amount,
                "currency": currency,
                "category": category,
                "payment": payment,
                "date": date_str,
                "description": description,
                "usd_amount": usd_amount
            }
            
            self.update_table()
            self.update_summary()
            self.update_charts()
            self.save_expenses()
            window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
    
    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        indices = [self.tree.index(item) for item in selected]
        indices = [i for i in indices if i < len(self.expenses)]  # Exclude summary row
        
        if not indices:
            return
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {len(indices)} expense(s)?"
        )
        
        if confirm:
            # Delete in reverse order to avoid index shifting issues
            for i in sorted(indices, reverse=True):
                del self.expenses[i]
            
            self.update_table()
            self.update_summary()
            self.update_charts()
            self.save_expenses()
    
    def clear_fields(self):
        self.amount_entry.delete(0, tk.END)
        self.currency_var.current(0)
        self.category_var.current(0)
        self.payment_var.current(0)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.desc_entry.delete(0, tk.END)
    
    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        total_usd = 0
        
        for expense in self.expenses:
            self.tree.insert("", "end", values=(
                f"{expense['amount']:.2f}",
                expense['currency'],
                expense['category'],
                expense['payment'],
                expense['date'],
                expense['description'],
                f"{expense['usd_amount']:.2f}"
            ))
            total_usd += expense['usd_amount']
        
        # Add total row
        self.tree.insert("", "end", values=(
            f"{sum(exp['amount'] for exp in self.expenses):.2f}",
            "Total",
            "",
            "",
            "",
            "",
            f"{total_usd:.2f}"
        ), tags=("total",))
        
        self.tree.tag_configure("total", background="#e6f3ff", font=('Helvetica', 10, 'bold'))
    
    def update_summary(self):
        if not self.expenses:
            for label in self.summary_labels.values():
                label.config(text="N/A")
            return
        
        # Total expenses
        total_usd = sum(exp['usd_amount'] for exp in self.expenses)
        self.summary_labels["Total Expenses (USD)"].config(text=f"${total_usd:.2f}")
        
        # This month's expenses
        current_month = datetime.now().strftime('%Y-%m')
        monthly_exp = sum(
            exp['usd_amount'] for exp in self.expenses 
            if exp['date'].startswith(current_month)
        )
        self.summary_labels["This Month"].config(text=f"${monthly_exp:.2f}")
        
        # Most spent category
        categories = {}
        for exp in self.expenses:
            categories[exp['category']] = categories.get(exp['category'], 0) + exp['usd_amount']
        if categories:
            top_category = max(categories.items(), key=lambda x: x[1])
            self.summary_labels["Most Spent Category"].config(text=f"{top_category[0]} (${top_category[1]:.2f})")
        
        # Top payment method
        payments = {}
        for exp in self.expenses:
            payments[exp['payment']] = payments.get(exp['payment'], 0) + 1
        if payments:
            top_payment = max(payments.items(), key=lambda x: x[1])
            self.summary_labels["Top Payment Method"].config(text=f"{top_payment[0]} ({top_payment[1]}x)")
    
    def update_charts(self):
        # Clear previous charts
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if not self.expenses:
            ttk.Label(self.chart_frame, text="No data to display").pack(expand=True)
            return
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
        fig.set_facecolor('#f0f0f0')
        
        # Category pie chart
        categories = {}
        for exp in self.expenses:
            categories[exp['category']] = categories.get(exp['category'], 0) + exp['usd_amount']
        
        if categories:
            ax1.pie(
                categories.values(), 
                labels=categories.keys(), 
                autopct='%1.1f%%',
                startangle=90,
                wedgeprops={'edgecolor': 'white'}
            )
            ax1.set_title('Expenses by Category')
        
        # Monthly trend chart
        months = {}
        for exp in self.expenses:
            month = exp['date'][:7]  # YYYY-MM
            months[month] = months.get(month, 0) + exp['usd_amount']
        
        if months:
            sorted_months = sorted(months.items())
            ax2.plot(
                [m[0] for m in sorted_months],
                [m[1] for m in sorted_months],
                marker='o'
            )
            ax2.set_title('Monthly Spending Trend')
            ax2.set_ylabel('Amount (USD)')
            plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
        
        # Embed in Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)
    
    def load_expenses(self):
        try:
            if os.path.exists('expenses.json'):
                with open('expenses.json', 'r') as f:
                    self.expenses = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load expenses: {e}")
    
    def save_expenses(self):
        try:
            with open('expenses.json', 'w') as f:
                json.dump(self.expenses, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save expenses: {e}")
    
    def export_csv(self):
        if not self.expenses:
            messagebox.showwarning("Warning", "No expenses to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save as CSV"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.expenses[0].keys())
                writer.writeheader()
                writer.writerows(self.expenses)
            
            messagebox.showinfo("Success", f"Expenses exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {e}")
    
    def export_json(self):
        if not self.expenses:
            messagebox.showwarning("Warning", "No expenses to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save as JSON"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                json.dump(self.expenses, f, indent=2)
            
            messagebox.showinfo("Success", f"Expenses exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export JSON: {e}")
    
    def generate_report(self):
        if not self.expenses:
            messagebox.showwarning("Warning", "No expenses to generate report")
            return
        
        report_win = tk.Toplevel(self.root)
        report_win.title("Expense Report")
        report_win.geometry("800x600")
        
        # Create text widget
        text_frame = ttk.Frame(report_win)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(
            text_frame, 
            yscrollcommand=scrollbar.set,
            font=('Courier', 10),
            padx=10,
            pady=10
        )
        text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text.yview)
        
        # Generate report content
        total = sum(exp['usd_amount'] for exp in self.expenses)
        current_month = datetime.now().strftime('%Y-%m')
        monthly_total = sum(
            exp['usd_amount'] for exp in self.expenses 
            if exp['date'].startswith(current_month)
        )
        
        # Categories breakdown
        categories = {}
        for exp in self.expenses:
            categories[exp['category']] = categories.get(exp['category'], 0) + exp['usd_amount']
        
        # Payment methods breakdown
        payments = {}
        for exp in self.expenses:
            payments[exp['payment']] = payments.get(exp['payment'], 0) + exp['usd_amount']
        
        # Generate report text
        report = [
            "EXPENSE TRACKER REPORT",
            "=" * 40,
            f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nTotal Expenses: ${total:.2f} USD",
            f"Current Month ({current_month}): ${monthly_total:.2f} USD",
            "\nCATEGORIES BREAKDOWN:",
            "-" * 40
        ]
        
        for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total) * 100
            report.append(f"{category:<20} ${amount:>10.2f} ({percentage:.1f}%)")
        
        report.extend([
            "\nPAYMENT METHODS:",
            "-" * 40
        ])
        
        for payment, amount in sorted(payments.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total) * 100
            report.append(f"{payment:<20} ${amount:>10.2f} ({percentage:.1f}%)")
        
        report.extend([
            "\nRECENT EXPENSES:",
            "-" * 40,
            f"{'Date':<12} {'Category':<15} {'Amount':>10} {'Currency':<8} {'Payment':<15} {'Description'}",
            "-" * 80
        ])
        
        for exp in sorted(self.expenses[-10:], key=lambda x: x['date'], reverse=True):
            report.append(
                f"{exp['date']:<12} {exp['category']:<15} {exp['amount']:>10.2f} "
                f"{exp['currency']:<8} {exp['payment']:<15} {exp['description']}"
            )
        
        text.insert(tk.END, "\n".join(report))
        text.config(state=tk.DISABLED)
        
        # Save button
        save_button = ttk.Button(
            report_win,
            text="Save Report",
            command=lambda: self.save_text_report(text.get("1.0", tk.END))
        )
        save_button.pack(pady=10)
    
    def save_text_report(self, content):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Save Report"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            
            messagebox.showinfo("Success", f"Report saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")

def main():
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()