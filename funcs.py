import plotly
import plotly.graph_objs as go
from datetime import datetime
from yahooquery import Ticker


def getStockData(symbol):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    change = data['regularMarketChange']
    percent_change = data['regularMarketChangePercent']*100

    if change >= 0:
        color = 'text-success'
    else:
        color = 'text-danger'

    data = {
        'symbol': symbol,
        'open': data['regularMarketOpen'],
        'previousClose': data['regularMarketPreviousClose'],
        'high': data['regularMarketDayHigh'],
        'low': data['regularMarketDayLow'],
        'lastPrice': data['regularMarketPrice'],
        'change': round(change, 2),
        'percent': round(percent_change, 2),
        'color': color,
    }

    return data


def getInventoryData(symbol, ownedPrice, priceWhenBuyed, quantity, id):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    lastPrice = data['regularMarketPrice']
    gainOrLoss = round(lastPrice - priceWhenBuyed, 4) * quantity
    gainOrLossPercent = (lastPrice - priceWhenBuyed) / lastPrice * 100

    if gainOrLoss >= 0:
        colorForGainLoss = 'text-success'
    else:
        colorForGainLoss = 'text-danger'

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
        'colorForGainLoss': colorForGainLoss,
    }

    return data


def getTicker(symbol):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

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
