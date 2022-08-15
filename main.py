import json
import time
import threading
from flask import request, render_template, url_for, redirect, flash
from flask_login import login_required, current_user, login_user, logout_user
from passlib.hash import sha256_crypt
from . import app, db, socketio
from .models import User, Market, Inventory
from .funcs import *
from yahooquery import Ticker
from threading import Timer, Thread


@app.route("/")
@login_required
def index():
    balance = round(current_user.balance, 5)
    inventory_list = Inventory.query.filter_by(
        owner_id=current_user.id).limit(3).all()
    market_list = Market.query.limit(3).all()

    return render_template(
        # html file
        "index.html",
        # template
        name=current_user.username,
        title='Overview',
        balance=balance,
        inventory_list=inventory_list,
        market_list=market_list
    )


@app.route("/sell", methods=['POST'])
def sell():
    amount = request.form.get("amount")
    inventory_id = request.form.get("inventory_id")
    symbol = request.form.get("symbol")

    try:
        item = Inventory.query.filter_by(
            id=inventory_id, owner_id=current_user.id).first()

        ticker = Ticker(symbol)
        data = ticker.price[symbol]
        lastPrice = data['regularMarketPrice']
        price = lastPrice * float(amount)
        current_user.balance += price

        db.session.delete(item)
        db.session.commit()

        flash('Successfly selled your stock!', category='success')
        return redirect(url_for('inventory'))
    except:
        flash('Wrong symbol.', category='danger')
        return redirect(url_for('inventory'))


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
    # chart
    fig = createStockChart(item.symbol)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    data = getInventoryData(
        item.symbol, item.ownedPrice, item.priceWhenBuyed, item.quantity, item.id)
    data['date'] = item.date
    return render_template("single_inventory.html", title='Owned - ' + item.symbol, graphJSON=graphJSON, data=data)


@app.route("/market")
@socketio.on('update')
@login_required
def market():
    stocks = []
    market_list = Market.query.all()
    for market_data in market_list:
        data = getStockData(market_data.symbol)
        stocks.append(data)

    return render_template("market.html", title='Market', stocks=stocks)


@app.route("/market/add", methods=['POST'])
@login_required
def market_add():
    if request.method == 'POST':
        symbol = request.form.get("stock-symbol")
        try:
            ticker = getTicker(symbol)
            new_stock = Market(
                symbol=symbol,
                openToday=ticker['regularMarketOpen'],
                previousClose=ticker['regularMarketPreviousClose'],
                averageVolume=ticker['regularMarketVolume'],
            )
        except:
            flash('Wrong symbol.', category='danger')
            return redirect(url_for('market'))

        db.session.merge(new_stock)
        db.session.commit()
        flash('Successfly added new stock to your market!', category='success')
        return redirect(url_for('market'))
    else:
        flash('Wrong request. Only POST allowed.', category='danger')
        return redirect(url_for('market'))


class RepeatTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.daemon = True
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


@app.route("/market/<string:Symbol>")
@socketio.on('update')
@login_required
def stock_info(Symbol):
    fig = createStockChart(Symbol)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    tmplData = getStockData(Symbol)
    amount = amountUserCanAfford(
        current_user.balance, tmplData['lastPrice'])

    '''
    @socketio.on('connect')
    def socket_update(data):
        live_data = getStockData(Symbol)
        timer = RepeatTimer(5, socket_update, live_data)
        timer.start()
        if data != tmplData:
            socketio.emit('liveData', data=data)
    '''

    return render_template(
        "single_market.html",
        title='Info',
        graphJSON=graphJSON,
        data=tmplData,
        amount=amount
    )


@app.route('/market/buy/<string:Symbol>', methods=['POST'])
@login_required
def stock_buy(Symbol):
    data = getStockData(Symbol)
    amount = int(request.form.get('amount'))
    if amount <= 0:
        flash("Amount cannot be 0.", category='danger')
        return redirect(url_for('market'))

    lastPrice = data['lastPrice']
    buyingPrice = amount * lastPrice
    balance = current_user.balance
    if balance < buyingPrice:
        flash("You don't have enough money for buying this stock.", category='danger')
        return redirect(url_for('market'))
    else:
        current_user.balance = balance - buyingPrice

        gainOrLoss = round(lastPrice - buyingPrice, 4) * amount
        gainOrLossPercent = (lastPrice - buyingPrice) / lastPrice * 100

        inv = Inventory(
            symbol=Symbol,
            ownedPrice=buyingPrice,
            quantity=amount,
            priceWhenBuyed=lastPrice,
            gainOrLoss=gainOrLoss,
            gainOrLossPercent=gainOrLossPercent,
            owner_id=current_user.id
        )

        db.session.add(inv)
        db.session.commit()

        flash("Sucessfly buyed a stock.", category='success')
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
