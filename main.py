from flask import request, render_template, url_for, redirect, flash
from flask_login import login_required, current_user, login_user, logout_user
from passlib.hash import sha256_crypt
from . import app, db
from .models import User, Market, Inventory
from .funcs import *
import yfinance as yf
from yahooquery import Ticker


@app.route("/")
@login_required
def index():
    # data = yf.download(['AAPL', 'TSLA', 'GOOGL', 'META'], period="1m", interval='15m', group_by='ticker')
    balance = round(current_user.balance, 5)
    return render_template("index.html", name=current_user.username, title='Overview', balance=balance)


@app.route("/inventory")
@login_required
def inventory():
    inventory = Inventory.query.filter_by(owner_id=current_user.id).all()
    tickers = Ticker(getSymbols(), asynchronous=True)
    df = tickers.history(period='1d', interval='1m')
    latest = df['close'].iloc[-1:]
    print(df)

    return render_template("inventory.html", title='Inventory', inventory=inventory)


@app.route("/market")
@login_required
def market():
    dicts = []
    market_list = Market.query.all()
    for market_data in market_list:
        data = Ticker(market_data.symbol, asynchronous=True).history(
            period='1d', interval='1m')
        # percent = % change
        change = data['open'][0] - data['close'][1]
        percent_change = (change/data['open'][1])*100
        if change >= 0:
            color = 'text-success'
        else:
            color = 'text-danger'

        current = {
            'ID': market_data.id,
            'Symbol': market_data.symbol,
            'High': data['high'][0],
            'Low': data['low'][0],
            'LastPrice': round(data['open'].iloc[-1], 2),
            'Open': data['open'][0],
            'Close': data['close'][0],
            'Change': round(change, 3),
            'Percent': round(percent_change, 2),
            'Color': color
        }
        dicts.append(current)

    return render_template("market.html", title='Market', dicts=dicts)


@app.route("/market/add", methods=['POST'])
@login_required
def market_add():
    if request.method == 'POST':
        symbol = request.form.get("stock-symbol")
        if symbol == '':
            flash('Wrong symbol.', category='danger')
            return redirect(url_for('market'))
        ticker = yf.Ticker(symbol)
        new_stock = Market(
            symbol=symbol,
            openToday=ticker.info['open'],
            previousClose=ticker.info['regularMarketPreviousClose'],
            averageVolume=ticker.info['averageVolume'],
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
    data = Ticker(stock.symbol, asynchronous=True).history(
            period='1d', interval='1m')
    #data = Ticker(stock.symbol)
    #print(tick.price)
    

    # percent = percent of change due to last price
    change = data['close'].iloc[-1] - stock.previousClose
    percent_change = (change/data['close'].iloc[-1])*100
    if change >= 0:
        color = 'text-success'
    else:
        color = 'text-danger'

    data = {
        'ID': stock.id,
        'Symbol': stock.symbol,
        'Open': data['open'].iloc[-1],
        'Close': data['close'].iloc[-1],
        'High': data['high'][0],
        'Low': data['low'][0],
        'LastPrice': round(data['open'].iloc[-1], 2),
        'Change': round(change, 2),
        'Percent': round(percent_change, 2),
        'Color': color
    }

    return render_template("single.html", title='Info', data=data, id=Id)


@app.route('/market/buy/<int:Id>', methods=['POST'])
@login_required
def stock_buy(Id):
    stock = Market.query.filter_by(id=Id).first()
    data = Ticker(stock.symbol, asynchronous=True).history(
            period='1d', interval='1m')
    amount = int(request.form.get('amount'))
    if amount <= 0:
        flash("Amount cannot be 0.", category='danger')
        return redirect(url_for('market'))
    stockPrice = round(data['open'].iloc[-1], 2)
    buyingPrice = amount * stockPrice
    balance = current_user.balance
    if balance < buyingPrice:
        flash("You don't have enough money for buying this stock.", category='danger')
        return redirect(url_for('market'))
    else:
        current_user.balance = balance - buyingPrice
        inv = Inventory(stock=stock.symbol, ownedPrice=buyingPrice, priceWhenBuyed=stockPrice, currentPrice=stockPrice,
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
