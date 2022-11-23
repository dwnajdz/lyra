from datetime import datetime
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(1000))
    password = db.Column(db.String(100))
    balance = db.Column(db.Float, default=212.14)

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = password


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(1000), nullable=False)
    ownedPrice = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    priceWhenBuyed = db.Column(db.Float, nullable=False)
    gainOrLoss = db.Column(db.Float)
    gainOrLossPercent = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Market(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(100), unique=True)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Float)
    date = db.Column(db.DateTime, nullable=False,
                     default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
