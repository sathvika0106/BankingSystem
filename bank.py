import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",       
    password="sath",  
    database="bankingdb"
)

cursor = conn.cursor()

def create_account(name, balance):
    query = "INSERT INTO accounts (name, balance) VALUES (%s, %s)"
    cursor.execute(query, (name, balance))
    conn.commit()
    print("✅ Account created successfully!")

def deposit(acc_no, amount):
    query = "UPDATE accounts SET balance = balance + %s WHERE acc_no = %s"
    cursor.execute(query, (amount, acc_no))
    conn.commit()
    print("✅ Deposit successful!")

def withdraw(acc_no, amount):
    # check balance first
    cursor.execute("SELECT balance FROM accounts WHERE acc_no = %s", (acc_no,))
    result = cursor.fetchone()
    if result and result[0] >= amount:
        query = "UPDATE accounts SET balance = balance - %s WHERE acc_no = %s"
        cursor.execute(query, (amount, acc_no))
        conn.commit()
        print("✅ Withdrawal successful!")
    else:
        print("❌ Insufficient balance!")

def check_balance(acc_no):
    cursor.execute("SELECT name, balance FROM accounts WHERE acc_no = %s", (acc_no,))
    result = cursor.fetchone()
    if result:
        print(f"👤 Name: {result[0]}, 💰 Balance: {result[1]}")
    else:
        print("❌ Account not found!")

# Menu
while True:
    print("\n=== Banking System ===")
    print("1. Create Account")
    print("2. Deposit")
    print("3. Withdraw")
    print("4. Check Balance")
    print("5. Exit")

    choice = input("Enter choice: ")

    if choice == '1':
        name = input("Enter name: ")
        balance = float(input("Enter initial balance: "))
        create_account(name, balance)
    elif choice == '2':
        acc_no = int(input("Enter account number: "))
        amount = float(input("Enter amount to deposit: "))
        deposit(acc_no, amount)
    elif choice == '3':
        acc_no = int(input("Enter account number: "))
        amount = float(input("Enter amount to withdraw: "))
        withdraw(acc_no, amount)
    elif choice == '4':
        acc_no = int(input("Enter account number: "))
        check_balance(acc_no)
    elif choice == '5':
        print("👋 Thank you for using Banking System")
        break
    else:
        print("❌ Invalid choice! Try again.")
