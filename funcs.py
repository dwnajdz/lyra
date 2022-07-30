from yahooquery import Ticker


def getStockData(symbol, id):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    change = data['regularMarketChange']
    percent_change = data['regularMarketChangePercent']*100

    if change >= 0:
        color = 'text-success'
    else:
        color = 'text-danger'

    data = {
        'ID': id,
        'Symbol': symbol,
        'Open': data['regularMarketOpen'],
        'previousClose': data['regularMarketPreviousClose'],
        'High': data['regularMarketDayHigh'],
        'Low': data['regularMarketDayLow'],
        'LastPrice': data['regularMarketPrice'],
        'Change': round(change, 2),
        'Percent': round(percent_change, 2),
        'Color': color,
    }

    return data


def getInventoryData(symbol, ownedPrice, priceWhenBuyed, quantity, id):
    ticker = Ticker(symbol)
    data = ticker.price[symbol]

    lastPrice = data['regularMarketPrice']
    gainOrLoss = round(lastPrice - priceWhenBuyed, 4)
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
