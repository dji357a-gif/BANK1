import os
import json
import random
import time
import getpass
from datetime import datetime, timedelta

# --- НАЛАШТУВАННЯ ТА КОНСТАНТИ ---
DB_FILE = "bank_data.json"
EXCHANGE_RATE = 41.5

# Кольори для консолі (ANSI)
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# --- СИСТЕМА ДАНИХ (Заміна SQL) ---
class Database:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if not os.path.exists(DB_FILE):
            return {"users": {}}
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}}

    def save(self):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4)

    def get_user(self, username):
        return self.data["users"].get(username)

    def create_user(self, username, password):
        if username in self.data["users"]:
            return False
        
        # Генерація картки
        card_number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        formatted_card = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
        
        self.data["users"][username] = {
            "password": password,
            "card_number": card_number,  # Зберігаємо без пробілів для пошуку
            "card_view": formatted_card, # Для краси
            "cvv": str(random.randint(100, 999)),
            "expiry": f"{random.randint(1, 12):02d}/{str(datetime.now().year + 3)[2:]}",
            "usd": 1000.0,
            "uah": 0.0,
            "credit_debt": 0.0,
            "credit_due_timestamp": None,
            "transactions": [],
            "portfolio": {}, # Крипта
            "deposits": []   # Вклади
        }
        self.save()
        return True

    def find_user_by_card(self, card_number):
        clean_card = card_number.replace(" ", "")
        for username, data in self.data["users"].items():
            if data["card_number"] == clean_card:
                return username
        return None

# --- БІЗНЕС ЛОГІКА ---
class BankSystem:
    def __init__(self):
        self.db = Database()
        self.current_user = None
        # Імітація біржі
        self.cryptos = {
            "BTC": 88079.58,
            "ETH": 2987.31,
            "XRP": 1.86,
            "SOL": 125.07
        }

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_logo(self):
        print(f"{Color.BLUE}{Color.BOLD}")
        print("╔══════════════════════════════════════╗")
        print("║          SOLID BANK PRO (CLI)        ║")
        print("╚══════════════════════════════════════╝")
        print(f"{Color.END}")

    def register(self):
        self.clear_screen()
        self.print_logo()
        print(">>> РЕЄСТРАЦІЯ")
        username = input("Логін: ")
        if not username: return
        password = input("Пароль: ")
        
        if self.db.create_user(username, password):
            print(f"{Color.GREEN}Успішно! Увійдіть у систему.{Color.END}")
            input("Натисніть Enter...")
        else:
            print(f"{Color.FAIL}Такий користувач вже існує.{Color.END}")
            time.sleep(2)

    def login(self):
        self.clear_screen()
        self.print_logo()
        print(">>> ВХІД")
        username = input("Логін: ")
        password = input("Пароль: ")

        user = self.db.get_user(username)
        if user and user["password"] == password:
            self.current_user = username
            self.check_credit_status() # Перевірка штрафів при вході
            self.check_deposits()      # Перевірка депозитів
            return True
        else:
            print(f"{Color.FAIL}Невірні дані.{Color.END}")
            time.sleep(1)
            return False

    def check_credit_status(self):
        # Логіка штрафів
        user = self.db.data["users"][self.current_user]
        if user["credit_debt"] > 0 and user["credit_due_timestamp"]:
            if time.time() > user["credit_due_timestamp"]:
                # Минуло 10 хвилин (600 сек)
                intervals = int((time.time() - user["credit_due_timestamp"]) / 600)
                if intervals > 0:
                    old_debt = user["credit_debt"]
                    user["credit_debt"] *= (1.10 ** intervals) # +10%
                    user["credit_due_timestamp"] = time.time() + 600 # Скидаємо таймер
                    print(f"{Color.FAIL}!!! УВАГА: Прострочення кредиту! Борг зріс з ${old_debt:.2f} до ${user['credit_debt']:.2f}{Color.END}")
                    self.db.save()
                    input("Enter щоб продовжити...")

    def check_deposits(self):
        # Логіка авто-виплати депозитів
        user = self.db.data["users"][self.current_user]
        active_deposits = []
        payout = 0
        
        for dep in user["deposits"]:
            if time.time() >= dep["end_timestamp"]:
                # Час вийшов, виплачуємо
                profit = dep["amount"] * 0.05
                total = dep["amount"] + profit
                user["usd"] += total
                payout += total
                user["transactions"].append(f"DEPOSIT PAYOUT: +${total:.2f}")
            else:
                active_deposits.append(dep)
        
        if payout > 0:
            user["deposits"] = active_deposits
            self.db.save()
            print(f"{Color.GREEN}>>> ДЕПОЗИТ ЗАВЕРШЕНО! Виплачено ${payout:.2f}{Color.END}")
            input("Enter...")

    # --- ГОЛОВНЕ МЕНЮ ---
    def dashboard(self):
        while True:
            self.clear_screen()
            user = self.db.data["users"][self.current_user]
            
            # 1. Відображення Картки (ASCII Art)
            print(f"{Color.BOLD}Ласкаво просимо, {self.current_user}!{Color.END}\n")
            print(f"{Color.FAIL}┌─────────────────────────────────────────┐")
            print(f"│ {Color.BOLD}SOLID BANK{Color.END}                {Color.CYAN}VISA Platinum{Color.END}{Color.FAIL} │")
            print(f"│                                         │")
            print(f"│   [====]  )))                           │")
            print(f"│                                         │")
            print(f"│   {Color.BOLD}{user['card_view']}{Color.END}{Color.FAIL}           │")
            print(f"│                                         │")
            print(f"│   {self.current_user.upper()}                   {user['expiry']}     │")
            print(f"└─────────────────────────────────────────┘{Color.END}")
            print(f"CVV: {user['cvv']} (Тільки для вас)")
            
            # 2. Баланси
            print(f"\n💵 USD: {Color.GREEN}${user['usd']:.2f}{Color.END}  |  ₴ UAH: {Color.CYAN}₴{user['uah']:.2f}{Color.END}")
            
            if user['credit_debt'] > 0:
                print(f"{Color.FAIL}⚠ БОРГ: ${user['credit_debt']:.2f}{Color.END}")

            print("\nМеню:")
            print("1. 💸 Переказати на картку")
            print("2. 💱 Обмін валют")
            print("3. 🏦 Кредити")
            print("4. 📈 Біржа та Депозити")
            print("5. 📜 Історія")
            print("0. Вихід")

            choice = input("\n>> ")

            if choice == "1": self.transfer_menu()
            elif choice == "2": self.exchange_menu()
            elif choice == "3": self.credit_menu()
            elif choice == "4": self.invest_menu()
            elif choice == "5": self.history_menu()
            elif choice == "0": break

    # --- ФУНКЦІЇ МЕНЮ ---
    def transfer_menu(self):
        print("\n--- ПЕРЕКАЗ ---")
        card = input("Номер картки отримувача (16 цифр): ").replace(" ", "")
        receiver_name = self.db.find_user_by_card(card)
        
        if not receiver_name:
            print(f"{Color.FAIL}Картку не знайдено!{Color.END}")
            input(); return
        
        if receiver_name == self.current_user:
            print(f"{Color.FAIL}Не можна переказувати собі!{Color.END}")
            input(); return

        try:
            amount = float(input("Сума переказу (USD): "))
            user = self.db.data["users"][self.current_user]
            receiver = self.db.data["users"][receiver_name]

            if user["usd"] >= amount and amount > 0:
                user["usd"] -= amount
                receiver["usd"] += amount
                
                user["transactions"].append(f"Переказ до {receiver_name}: -${amount:.2f}")
                receiver["transactions"].append(f"Вхідний від {self.current_user}: +${amount:.2f}")
                
                self.db.save()
                print(f"{Color.GREEN}Успішно!{Color.END}")
            else:
                print(f"{Color.FAIL}Недостатньо коштів.{Color.END}")
        except ValueError:
            print("Невірне число.")
        input("Enter...")

    def exchange_menu(self):
        print("\n--- ОБМІН (Курс 41.5) ---")
        print("1. Купити UAH (Продати USD)")
        print("2. Купити USD (Продати UAH)")
        choice = input(">> ")
        
        try:
            amount = float(input("Сума: "))
            user = self.db.data["users"][self.current_user]

            if choice == "1":
                if user["usd"] >= amount:
                    user["usd"] -= amount
                    received = amount * EXCHANGE_RATE
                    user["uah"] += received
                    print(f"{Color.GREEN}Обміняно! Отримано {received:.2f} UAH{Color.END}")
                else:
                    print(f"{Color.FAIL}Мало USD{Color.END}")
            elif choice == "2":
                if user["uah"] >= amount:
                    user["uah"] -= amount
                    received = amount / EXCHANGE_RATE
                    user["usd"] += received
                    print(f"{Color.GREEN}Обміняно! Отримано {received:.2f} USD{Color.END}")
                else:
                    print(f"{Color.FAIL}Мало UAH{Color.END}")
            
            self.db.save()
        except: pass
        input("Enter...")

    def credit_menu(self):
        user = self.db.data["users"][self.current_user]
        print(f"\n--- КРЕДИТНЕ БЮРО ---")
        if user["credit_debt"] > 0:
            print(f"Ваш борг: {Color.FAIL}${user['credit_debt']:.2f}{Color.END}")
            print("1. Погасити борг")
            if input(">> ") == "1":
                if user["usd"] >= user["credit_debt"]:
                    user["usd"] -= user["credit_debt"]
                    user["credit_debt"] = 0
                    user["credit_due_timestamp"] = None
                    self.db.save()
                    print(f"{Color.GREEN}Борг погашено! Ви вільні.{Color.END}")
                else:
                    print(f"{Color.FAIL}Не вистачає USD для погашення.{Color.END}")
        else:
            print("Ви можете взяти кредит на 10 хвилин.")
            try:
                amt = float(input("Сума кредиту: "))
                if amt > 0:
                    fee = amt * 0.05
                    user["usd"] += amt
                    user["credit_debt"] = amt + fee
                    user["credit_due_timestamp"] = time.time() + 600 # 10 хв
                    self.db.save()
                    print(f"{Color.GREEN}Кредит видано! Поверніть ${user['credit_debt']} за 10 хв.{Color.END}")
            except: pass
        input("Enter...")

    def invest_menu(self):
        while True:
            self.clear_screen()
            user = self.db.data["users"][self.current_user]
            
            # Симуляція зміни цін
            for coin in self.cryptos:
                change = random.uniform(-0.02, 0.02)
                self.cryptos[coin] *= (1 + change)

            print(f"{Color.CYAN}--- БІРЖА & ДЕПОЗИТИ ---{Color.END}")
            print("Монети (Жива ціна):")
            for coin, price in self.cryptos.items():
                owned = user["portfolio"].get(coin, 0.0)
                print(f"  {coin}: ${price:.2f} | У вас: {owned:.4f}")

            print("\nАктивні депозити:")
            if not user["deposits"]: print("  (Немає)")
            for i, dep in enumerate(user["deposits"]):
                left = int(dep["end_timestamp"] - time.time())
                print(f"  #{i+1}: ${dep['amount']} (Залишилось {left} сек)")

            print("\n1. Купити Крипту")
            print("2. Продати Крипту")
            print("3. Відкрити Депозит (2 хв, +5%)")
            print("0. Назад")
            
            ch = input(">> ")
            if ch == "0": break
            
            if ch == "1": # BUY
                coin = input("Символ (BTC/ETH/XRP/SOL): ").upper()
                if coin in self.cryptos:
                    try:
                        amt = float(input("Кількість монет: "))
                        cost = amt * self.cryptos[coin]
                        if user["usd"] >= cost:
                            user["usd"] -= cost
                            user["portfolio"][coin] = user["portfolio"].get(coin, 0) + amt
                            print(f"{Color.GREEN}Куплено!{Color.END}")
                        else: print(f"{Color.FAIL}Мало грошей{Color.END}")
                    except: pass
            
            if ch == "3": # DEPOSIT
                try:
                    amt = float(input("Сума вкладу ($): "))
                    if user["usd"] >= amt and amt > 0:
                        user["usd"] -= amt
                        user["deposits"].append({
                            "amount": amt,
                            "end_timestamp": time.time() + 120 # 2 хвилини
                        })
                        print(f"{Color.GREEN}Депозит відкрито!{Color.END}")
                    else: print(f"{Color.FAIL}Мало грошей{Color.END}")
                except: pass
            
            self.db.save()
            if ch in ["1", "2", "3"]: input("Enter...")

    def history_menu(self):
        print("\n--- ІСТОРІЯ ---")
        user = self.db.data["users"][self.current_user]
        for t in reversed(user["transactions"][-10:]):
            print(t)
        input("Enter...")

    def run(self):
        while True:
            self.clear_screen()
            self.print_logo()
            print("1. Вхід")
            print("2. Реєстрація")
            print("0. Вихід")
            
            choice = input("\n>> ")
            
            if choice == "1":
                if self.login():
                    self.dashboard()
            elif choice == "2":
                self.register()
            elif choice == "0":
                print("Бувай!")
                break

if __name__ == "__main__":
    app = BankSystem()
    app.run()