# funcs.py is a file with all functions that doesn't require database data
import plotly
import plotly.graph_objs as go
from datetime import datetime
from yahooquery import Ticker


def setColor(value):
    if value >= 0:
        return 'text-success'
    return 'text-danger'


def getStockData(symbol):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    try:
        change = data['regularMarketChange']
        percent_change = data['regularMarketChangePercent']*100

        data = {
            'symbol': symbol,
            'open': data['regularMarketOpen'],
            'previousClose': data['regularMarketPreviousClose'],
            'high': data['regularMarketDayHigh'],
            'low': data['regularMarketDayLow'],
            'lastPrice': data['regularMarketPrice'],
            'change': round(change, 2),
            'percent': round(percent_change, 2),
            'color': setColor(change),
        }

        return data
    except:
        return None


def getInventoryData(symbol, ownedPrice, priceWhenBuyed, quantity, id):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    lastPrice = data['regularMarketPrice']
    gainOrLoss = round(lastPrice - priceWhenBuyed, 4) * quantity
    gainOrLossPercent = (lastPrice - priceWhenBuyed) / lastPrice * 100

    data = {
        'ID': id,
        'symbol': symbol,
        'pen': data['regularMarketOpen'],
        'previousClose': data['regularMarketPreviousClose'],
        'high': data['regularMarketDayHigh'],
        'low': data['regularMarketDayLow'],
        'lastPrice': lastPrice,
        'ownedPrice': ownedPrice,
        'quantity': quantity,
        'priceWhenBuyed': priceWhenBuyed,
        'gainOrLoss': gainOrLoss,
        'gainOrLossPercent': gainOrLossPercent,
        'colorForGainLoss': setColor(gainOrLoss),
    }

    return data


def createStockChart(symbol):
    ticker = Ticker(symbol)
    df = ticker.history()
    df = df.reset_index(level=[0, 1])

    fig = go.Figure(
        data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])

    return fig


def amountUserCanAfford(balance, price):
    amount = 0
    while True:
        if balance < price:
            break
        balance = balance - price
        amount += 1

    return amount
