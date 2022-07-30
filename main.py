from flask import request, render_template, url_for, redirect, flash
from flask_login import login_required, current_user, login_user, logout_user
from passlib.hash import sha256_crypt
from . import app, db
from .models import User, Market, Inventory
from .funcs import *


@app.route("/")
@login_required
def index():
    balance = round(current_user.balance, 5)
    return render_template("index.html", name=current_user.username, title='Overview', balance=balance)


@app.route("/inventory")
@login_required
def inventory():
    inventory = Inventory.query.filter_by(owner_id=current_user.id).all()
    stocks = []
    for item in inventory:
        data = getInventoryData(
            item.symbol, item.ownedPrice, item.priceWhenBuyed, item.quantity, item.id)
        stocks.append(data)

    return render_template("inventory.html", title='Inventory', inventory=stocks)


@app.route("/inventory/<int:Id>")
@login_required
def inventoryItem(Id):
    item = Inventory.query.filter_by(owner_id=current_user.id, id=Id).first()
    data = getInventoryData(
            item.symbol, item.ownedPrice, item.priceWhenBuyed, item.quantity, item.id)
    data['date'] = item.date
    return render_template("single_inventory.html", title='Owned - ' + item.symbol, data=data)


@app.route("/market")
@login_required
def market():
    stocks = []
    market_list = Market.query.all()
    for market_data in market_list:
        data = getStockData(market_data.symbol, market_data.id)
        stocks.append(data)

    return render_template("market.html", title='Market', stocks=stocks)


@app.route("/market/add", methods=['POST'])
@login_required
def market_add():
    if request.method == 'POST':
        symbol = request.form.get("stock-symbol")
        if symbol == '':
            flash('Wrong symbol.', category='danger')
            return redirect(url_for('market'))
        ticker = getTicker(symbol)
        new_stock = Market(
            symbol=symbol,
            openToday=ticker['regularMarketOpen'],
            previousClose=ticker['regularMarketPreviousClose'],
            averageVolume=ticker['regularMarketVolume'],
            # targetMedianPrice=ticker.info['targetMedianPrice']
        )

        db.session.merge(new_stock)
        db.session.commit()
        flash('Successfly added new stock to your market!', category='success')
        return redirect(url_for('market'))
    else:
        flash('Wrong request. Only POST allowed.', category='danger')
        return redirect(url_for('market'))


@app.route("/market/<int:Id>")
@login_required
def stock_info(Id):
    stock = Market.query.filter_by(id=Id).first()
    data = getStockData(stock.symbol, stock.id)

    return render_template("single_market.html", title='Info', data=data, id=Id)


@app.route('/market/buy/<int:Id>', methods=['POST'])
@login_required
def stock_buy(Id):
    stock = Market.query.filter_by(id=Id).first()
    data = getStockData(stock.symbol, stock.id)

    amount = int(request.form.get('amount'))
    if amount <= 0:
        flash("Amount cannot be 0.", category='danger')
        return redirect(url_for('market'))
    stockPrice = data['LastPrice']
    buyingPrice = amount * stockPrice
    balance = current_user.balance
    if balance < buyingPrice:
        flash("You don't have enough money for buying this stock.", category='danger')
        return redirect(url_for('market'))
    else:
        current_user.balance = balance - buyingPrice
        inv = Inventory(symbol=stock.symbol, ownedPrice=buyingPrice, quantity=amount, priceWhenBuyed=stockPrice, currentPrice=stockPrice,
                        owner_id=current_user.id)
        db.session.add(inv)
        db.session.commit()
        flash("You don't have enoug money for buying this stock.", category='success')
        return redirect(url_for('market'))


@app.route("/settings", methods=['POST', 'GET'])
@login_required
def settings():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        user = User.query.filter_by(email=email).first()

        if sha256_crypt.verify(old_password, user.password):
            user.email = email
            user.username = username
            user.password = sha256_crypt.encrypt(new_password)
            db.session.commit()
            flash('Successfly changed account details', category='success')
            return redirect(url_for('index'))
        else:
            flash('Please check your account details and try again.',
                  category='danger')
            return redirect(url_for('index'))

    return render_template("settings.html",  name=current_user.username, email=current_user.email, title='Settings')


@app.route('/login',)
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or not sha256_crypt.verify(password, user.password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))

    login_user(user, remember=remember)
    return redirect(url_for('index'))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email address already exists')
        return redirect(url_for('login'))

    new_acc = User(email=email, password=sha256_crypt.encrypt(
        password), username=username)

    db.session.add(new_acc)
    db.session.commit()

    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user
    return redirect(url_for('login'))
