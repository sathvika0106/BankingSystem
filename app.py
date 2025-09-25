from flask import Flask, render_template, request, redirect, session, flash
import hashlib, os
from db import get_db_connection

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Hash PIN with salt
def hash_pin(pin, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    pin_hash = hashlib.sha256((pin + salt).encode()).hexdigest()
    return salt, pin_hash


# ---------------- Home ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- Register ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin'].encode('utf-8')

        # Hash PIN using bcrypt
        pin_hash = bcrypt.hashpw(pin, bcrypt.gensalt()).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO customers (name, pin_salt, pin_hash) VALUES (%s, %s, %s)",
                    (name, '', pin_hash))
        conn.commit()

        # Get the newly generated account number
        acc_no = cur.lastrowid  

        cur.close()
        conn.close()

        flash(f"✅ Account created successfully! Your Account Number is: {acc_no}. Please note it for login.", "success")
        return redirect('/login')
    return render_template('register.html')



# ---------------- Login ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        acc_no = request.form['acc_no']
        pin = request.form['pin']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM customers WHERE acc_no=%s", (acc_no,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            salt = user['pin_salt']
            pin_hash = hashlib.sha256((pin + salt).encode()).hexdigest()
            if pin_hash == user['pin_hash']:
                session['user'] = user
                return redirect('/dashboard')
        flash("❌ Invalid Account No or PIN")
    return render_template('login.html')


# ---------------- Dashboard ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT balance FROM customers WHERE acc_no=%s", (session['user']['acc_no'],))
    balance = cur.fetchone()['balance']
    cur.close()
    conn.close()

    return render_template('dashboard.html', user=session['user'], balance=balance)


# ---------------- Deposit ----------------
@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    amount = float(request.form['amount'])
    acc_no = session['user']['acc_no']

    conn = get_db_connection()
    cur = conn.cursor()

    # Update balance
    cur.execute("UPDATE customers SET balance = balance + %s WHERE acc_no = %s", (amount, acc_no))

    # Insert into transactions
    cur.execute("INSERT INTO transactions (acc_no, type, amount) VALUES (%s, 'Deposit', %s)",
                (acc_no, amount))

    conn.commit()
    cur.close()
    conn.close()

    flash(f"✅ Deposited {amount:.2f} successfully!", "success")
    return redirect('/dashboard')

# ---------------- Withdraw ----------------
@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session:
        return redirect('/login')

    amount = float(request.form['amount'])
    acc_no = session['user']['acc_no']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Check balance
    cur.execute("SELECT balance FROM customers WHERE acc_no=%s", (acc_no,))
    bal = cur.fetchone()['balance']

    if bal < amount:
        flash("❌ Insufficient balance!", "error")
    else:
        cur.execute("UPDATE customers SET balance = balance - %s WHERE acc_no=%s", (amount, acc_no))
        cur.execute("INSERT INTO transactions (acc_no, type, amount) VALUES (%s, 'Withdraw', %s)",
                    (acc_no, amount))
        conn.commit()
        flash(f"✅ Withdrawn {amount:.2f} successfully!", "success")

    cur.close()
    conn.close()
    return redirect('/dashboard')


# ---------------- Transfer ----------------
@app.route('/transfer', methods=['POST'])
def transfer():
    if 'user' not in session:
        return redirect('/login')

    acc_no = session['user']['acc_no']
    target_acc = request.form['target_acc']
    amount = float(request.form['amount'])

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Check if target account exists
    cur.execute("SELECT balance FROM customers WHERE acc_no=%s", (target_acc,))
    target = cur.fetchone()
    if not target:
        flash("❌ Target account does not exist!", "error")
        cur.close()
        conn.close()
        return redirect('/dashboard')

    # Check source balance
    cur.execute("SELECT balance FROM customers WHERE acc_no=%s", (acc_no,))
    bal = cur.fetchone()['balance']

    if bal < amount:
        flash("❌ Insufficient balance for transfer!", "error")
    else:
        # Deduct from sender
        cur.execute("UPDATE customers SET balance = balance - %s WHERE acc_no=%s", (amount, acc_no))
        # Add to receiver
        cur.execute("UPDATE customers SET balance = balance + %s WHERE acc_no=%s", (amount, target_acc))

        # Insert transaction for sender
        cur.execute("INSERT INTO transactions (acc_no, type, amount, target_acc) VALUES (%s, 'Transfer', %s, %s)",
                    (acc_no, amount, target_acc))

        # Insert transaction for receiver
        cur.execute("INSERT INTO transactions (acc_no, type, amount, target_acc) VALUES (%s, 'Deposit', %s, %s)",
                    (target_acc, amount, acc_no))

        conn.commit()
        flash(f"✅ Transferred {amount:.2f} to Account {target_acc} successfully!", "success")

    cur.close()
    conn.close()
    return redirect('/dashboard')
# ---------------- Transactions ----------------
@app.route('/transactions')
def transactions():
    if 'user' not in session:
        return redirect('/login')

    acc_no = session['user']['acc_no']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM transactions WHERE acc_no=%s ORDER BY created_at DESC", (acc_no,))
    trans = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('transactions.html', transactions=trans)


# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
