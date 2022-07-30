from datetime import datetime
from enum import unique
from flask_login import UserMixin
from sqlalchemy import ForeignKey
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(1000))
    password = db.Column(db.String(100))
    balance = db.Column(db.Float, default=1000.00)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(1000), nullable=False)
    # ownedPrice is how much you spended on that stock
    ownedPrice = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # priceWhenBuyed is price of this as you were buying it
    priceWhenBuyed = db.Column(db.Float, nullable=False)
    # currentPrice is current price of stock
    # it is updated every time you enter /inventory
    currentPrice = db.Column(db.Float)
    gainOrLoss = db.Column(db.Float)
    gainOrLossPercent = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(100), unique=True)
    # added this columns below for faster market/<Id> page loading
    # and not downloading always the same static data
    #
    # columns below are always updated at the end of day
    openToday = db.Column(db.Integer)
    previousClose = db.Column(db.Integer)
    averageVolume = db.Column(db.Integer)
    #targetMedianPrice = db.Column(db.Integer)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float)
    # price collected at the end of the day
    price = db.Column(db.Integer)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow)
