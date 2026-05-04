import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# Конфигурация
API_KEY = "ed425364573391839dab9cb7"
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
HISTORY_FILE = "history.json"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # Загружаем курсы относительно USD
        self.rates = self.fetch_rates()
        if not self.rates:
            messagebox.showerror("Ошибка", "Не удалось загрузить курсы валют. Проверьте API-ключ.")
            root.destroy()
            return

        # Список доступных валют (все ключи словаря rates)
        self.currencies = list(self.rates.keys())

        # Загружаем историю из файла
        self.history = self.load_history()

        # --- GUI Элементы ---
        # Выбор исходной валюты
        ttk.Label(root, text="Из валюты:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.from_currency = ttk.Combobox(root, values=self.currencies, state="readonly")
        self.from_currency.grid(row=0, column=1, padx=10, pady=10)
        self.from_currency.set("USD")

        # Выбор целевой валюты
        ttk.Label(root, text="В валюту:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.to_currency = ttk.Combobox(root, values=self.currencies, state="readonly")
        self.to_currency.grid(row=1, column=1, padx=10, pady=10)
        self.to_currency.set("EUR")

        # Поле ввода суммы
        ttk.Label(root, text="Сумма:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.amount_entry = ttk.Entry(root)
        self.amount_entry.grid(row=2, column=1, padx=10, pady=10)
        self.amount_entry.insert(0, "1")

        # Кнопка конвертации
        ttk.Button(root, text="Конвертировать", command=self.convert).grid(row=3, column=0, columnspan=2, pady=10)

        # Метка для результата
        self.result_label = ttk.Label(root, text="Результат: ", font=("Arial", 12))
        self.result_label.grid(row=4, column=0, columnspan=2, pady=5)

        # Таблица истории
        ttk.Label(root, text="История конвертаций:").grid(row=5, column=0, columnspan=2, pady=(20,5), sticky="w")
        columns = ("Дата", "Из", "В", "Сумма", "Результат")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

        # Скроллбар для таблицы
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=6, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Заполняем таблицу сохранённой историей
        self.refresh_history_table()

    def fetch_rates(self):
        """Получает курсы валют относительно USD через API."""
        try:
            response = requests.get(BASE_URL, timeout=10)
            data = response.json()
            if data.get("result") == "success":
                return data["conversion_rates"]
            else:
                return None
        except Exception as e:
            print(f"Ошибка API: {e}")
            return None

    def convert(self):
        """Выполняет конвертацию валюты."""
        from_cur = self.from_currency.get()
        to_cur = self.to_currency.get()
        amount_str = self.amount_entry.get().strip()

        # Проверка корректности ввода суммы
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Сумма должна быть положительным числом")
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Введите положительное число (например, 100 или 99.95).")
            return

        # Конвертация через USD (двусторонняя)
        if from_cur not in self.rates or to_cur not in self.rates:
            messagebox.showerror("Ошибка", "Выбрана недопустимая валюта.")
            return

        # Количество USD, которое можно купить за amount единиц from_cur
        usd_amount = amount / self.rates[from_cur]
        # Результат в целевой валюте
        result = usd_amount * self.rates[to_cur]

        # Форматирование до 2 знаков после запятой
        result_text = f"{amount:.2f} {from_cur} = {result:.2f} {to_cur}"
        self.result_label.config(text="Результат: " + result_text)

        # Сохраняем запись в историю
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "from": from_cur,
            "to": to_cur,
            "amount": amount,
            "result": round(result, 2)
        }
        self.history.append(record)
        self.save_history()
        self.refresh_history_table()

    def load_history(self):
        """Загружает историю из JSON-файла."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self):
        """Сохраняет историю в JSON-файл."""
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def refresh_history_table(self):
        """Обновляет таблицу истории в GUI."""
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Добавляем записи (самые новые снизу)
        for entry in self.history:
            self.tree.insert("", "end", values=(
                entry["date"],
                entry["from"],
                entry["to"],
                entry["amount"],
                entry["result"]
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()