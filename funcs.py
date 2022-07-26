from .models import Market


def getSymbols():
    symbols = []
    market = Market.query.all()
    for stock in market:
        symbols.append(stock.symbol)

    return symbols
