from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime
from datetime import timezone
import os


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

# MongoDB configuration
app.config["MONGO_URI"] = os.environ.get('MONGO_URI', 'mongodb://mongo:27017/bank_app')
mongo = PyMongo(app)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not first_name or not last_name or not email or not password:
            flash('Please fill all fields', 'error')
            return redirect(url_for('register'))
        existing_user = mongo.db.users.find_one({'email': email})
        if existing_user:
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        password_hash = generate_password_hash(password)
        user = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password_hash': password_hash,
            'balance': 0,
            'transactions': []
        }
        mongo.db.users.insert_one(user)
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'email': email})
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = str(user['_id'])
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/api/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('dashboard.html', user=user)

@app.route('/api/deposit', methods=['POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    amount = request.form.get('amount')
    try:
        amount = float(amount)
    except:
        flash('Invalid amount', 'error')
        return redirect(url_for('dashboard'))
    if amount <= 0:
        flash('Amount must be positive', 'error')
        return redirect(url_for('dashboard'))
    if amount > 10000:
        flash('Amount above 10,000 requires OTP verification (skipped)', 'info')
        # OTP not implemented
    user_id = session['user_id']
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    new_balance = user['balance'] + amount
    transaction = {'type': 'deposit', 'amount': amount, 'date': datetime.datetime.now(datetime.timezone.utc)}
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
        '$set': {'balance': new_balance},
        '$push': {'transactions': transaction}
        }
    )
    #mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'balance': new_balance}, '$push': {'transactions': transaction}})
    flash('Deposit successful', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    amount = request.form.get('amount')
    try:
        amount = float(amount)
    except:
        flash('Invalid amount', 'error')
        return redirect(url_for('dashboard'))
    if amount <= 0:
        flash('Amount must be positive', 'error')
        return redirect(url_for('dashboard'))
    user_id = session['user_id']
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user['balance'] < amount:
        flash('Insufficient funds', 'error')
        return redirect(url_for('dashboard'))
    new_balance = user['balance'] - amount
    transaction = {'type': 'withdrawal', 'amount': amount, 'date': datetime.datetime.now(datetime.timezone.utc)}
    mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {
        '$set': {'balance': new_balance},
        '$push': {'transactions': transaction}
        }
    )
    #mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'balance': new_balance}, '$push': {'transactions': transaction}})
    flash('Withdrawal successful', 'success')
    return redirect(url_for('dashboard'))


def serialize_tx(t):
    return {
        'type': t['type'],
        'amount': t['amount'],
        'date': t['date'].isoformat()
    }

@app.route('/api/transactions', methods=['GET'], strict_slashes=False)
@app.route('/api/transactions/', methods=['GET'])
def get_transactions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    user_id = session['user_id']

    # During automated tests, use the mocked MongoDB database.
    if app.config.get('TESTING'):
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        grouped = {}
        for t in user.get('transactions', []):
            month = t['date'].strftime('%B %Y')
            grouped.setdefault(month, []).append(serialize_tx(t))

        return jsonify([
            {'month': month, 'transactions': transactions}
            for month, transactions in grouped.items()
        ])

    # In Docker, request the monthly report from Node.js.
    import json
    import urllib.request
    import urllib.error
    import calendar

    service_url = (
        'http://transactions:3000/api/transactions/' + user_id
    )

    try:
        with urllib.request.urlopen(service_url, timeout=5) as response:
            reports = json.load(response)

        result = []
        for group in reports:
            year = group['_id']['year']
            month_number = group['_id']['month']
            month = f"{calendar.month_name[month_number]} {year}"

            result.append({
                'month': month,
                'transactions': group['transactions']
            })

        return jsonify(result)

    except (urllib.error.URLError, ValueError, KeyError, TypeError) as error:
        app.logger.error('Transactions service error: %s', error)
        return jsonify({'error': 'Transactions service unavailable'}), 502


@app.route('/api/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
