import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Жильё", "Здоровье", "Одежда", "Другое"]
DATE_FORMAT = "%Y-%m-%d"
DATA_FILE = "expenses.json"

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x650")
        self.expenses = []
        self.load_data()
        self.setup_ui()

    def setup_ui(self):
        # --- Панель ввода ---
        input_frame = ttk.LabelFrame(self.root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.amount_var, width=12).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        ttk.Combobox(input_frame, textvariable=self.category_var, values=CATEGORIES, state="readonly", width=15).grid(row=0, column=3, padx=5, pady=5)
        self.category_var.set(CATEGORIES[0])

        ttk.Label(input_frame, text=f"Дата ({DATE_FORMAT}):").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.date_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.date_var, width=12).grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(input_frame, text="➕ Добавить расход", command=self.add_expense).grid(row=0, column=6, padx=10, pady=5)

        # --- Панель фильтрации и итогов ---
        filter_frame = ttk.LabelFrame(self.root, text="Фильтр и Подсчёт", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Категория:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.filter_cat_var = tk.StringVar(value="Все")
        ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, values=["Все"] + CATEGORIES, state="readonly", width=15).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text="С:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.start_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text="По:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.end_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.end_date_var, width=10).grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(filter_frame, text="🔍 Применить фильтр", command=self.apply_filters).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(filter_frame, text="↺ Сбросить", command=self.reset_filters).grid(row=0, column=7, padx=5, pady=5)
        ttk.Button(filter_frame, text="📊 Рассчитать за период", command=self.calculate_period_total).grid(row=0, column=8, padx=10, pady=5)

        self.total_label = ttk.Label(filter_frame, text="Итого: 0.00 ₽", font=("Arial", 11, "bold"), foreground="#27ae60")
        self.total_label.grid(row=0, column=9, padx=10, pady=5)

        # --- Таблица ---
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("ID", "Сумма", "Категория", "Дата")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Сумма", width=100, anchor="center")
        self.tree.column("Категория", width=140, anchor="center")
        self.tree.column("Дата", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.refresh_table(self.expenses)

        # --- Панель управления данными ---
        ctrl_frame = ttk.Frame(self.root, padding=(10, 5))
        ctrl_frame.pack(fill="x")
        ttk.Button(ctrl_frame, text="💾 Сохранить в JSON", command=self.save_data).pack(side="left", padx=10)
        ttk.Button(ctrl_frame, text="📂 Загрузить из JSON", command=self.load_data).pack(side="left", padx=10)
        ttk.Button(ctrl_frame, text="🗑 Очистить всё", command=self.clear_all).pack(side="left", padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def validate_input(self):
        amount_str = self.amount_var.get().strip().replace(",", ".")
        date_str = self.date_var.get().strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка валидации", "Сумма должна быть положительным числом.")
                return None
        except ValueError:
            messagebox.showerror("Ошибка валидации", "Сумма должна быть числом.")
            return None

        try:
            datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            messagebox.showerror("Ошибка валидации", f"Неверный формат даты. Используйте: {DATE_FORMAT}")
            return None

        return amount, date_str

    def add_expense(self):
        result = self.validate_input()
        if result is None: return

        amount, date_str = result
        new_id = len(self.expenses) + 1
        self.expenses.append({"id": new_id, "amount": amount, "category": self.category_var.get(), "date": date_str})
        self.save_data()
        self.refresh_table(self.expenses)
        self.clear_inputs()
        messagebox.showinfo("Успех", "Расход успешно добавлен!")

    def clear_inputs(self):
        self.amount_var.set("")
        self.date_var.set("")
        self.category_var.set(CATEGORIES[0])

    def refresh_table(self, data):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in sorted(data, key=lambda x: x["id"]):
            self.tree.insert("", "end", values=(item["id"], f"{item['amount']:.2f}", item["category"], item["date"]))

    def apply_filters(self):
        filtered = self.expenses[:]
        cat = self.filter_cat_var.get()
        if cat != "Все":
            filtered = [e for e in filtered if e["category"] == cat]

        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        if start or end:
            try:
                s = datetime.strptime(start, DATE_FORMAT) if start else None
                e = datetime.strptime(end, DATE_FORMAT) if end else None
                filtered = [x for x in filtered if (not s or datetime.strptime(x["date"], DATE_FORMAT) >= s) and (not e or datetime.strptime(x["date"], DATE_FORMAT) <= e)]
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты в фильтрах.")
                return

        self.refresh_table(filtered)
        self.calculate_total(filtered)

    def calculate_period_total(self):
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        if not start and not end:
            messagebox.showwarning("Внимание", "Укажите хотя бы одну дату для расчёта периода.")
            return
        try:
            s = datetime.strptime(start, DATE_FORMAT) if start else None
            e = datetime.strptime(end, DATE_FORMAT) if end else None
            period_data = [x for x in self.expenses if (not s or datetime.strptime(x["date"], DATE_FORMAT) >= s) and (not e or datetime.strptime(x["date"], DATE_FORMAT) <= e)]
            self.calculate_total(period_data)
            self.refresh_table(period_data)
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты.")

    def calculate_total(self, data):
        total = sum(e["amount"] for e in data)
        self.total_label.config(text=f"Итого: {total:.2f} ₽")

    def reset_filters(self):
        self.filter_cat_var.set("Все")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.refresh_table(self.expenses)
        self.calculate_total()

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, indent=2, ensure_ascii=False)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except json.JSONDecodeError:
                self.expenses = []
                messagebox.showwarning("Ошибка", "Файл JSON повреждён. Создан новый список.")
        else:
            self.expenses = []
        self.refresh_table(self.expenses)
        self.calculate_total()

    def clear_all(self):
        if messagebox.askyesno("Подтверждение", "Удалить все данные? Это действие нельзя отменить."):
            self.expenses.clear()
            self.save_data()
            self.refresh_table([])
            self.calculate_total()
            self.reset_filters()

    def on_closing(self):
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
