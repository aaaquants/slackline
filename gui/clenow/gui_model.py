import sys
sys.dont_write_bytecode = True
from wtforms import Form, FloatField, validators, StringField,IntegerField


class InputForm(Form):
    start = StringField(
        label='Start', default='2015-01-01',
        validators=[validators.InputRequired()])
    finish = StringField(
        label='Finish', default='2017-01-01',
        validators=[validators.InputRequired()])
    symbols = StringField(
        label='Symbols', default='MSFT,AAPL,IBM',
        validators=[validators.InputRequired()])
    risk_factor = FloatField(
        label='Risk Factor', default=0.001,
        validators=[validators.InputRequired()])
    atr_lkbk = IntegerField(
        label='ATR Lookback', default=20,
        validators=[validators.InputRequired()])
    lr_lkbk = IntegerField(
        label='Regression Lookback', default=200,
        validators=[validators.InputRequired()])
    ma_lkbk = IntegerField(
        label='MA Lookback', default=200,
        validators=[validators.InputRequired()])
    max_items = IntegerField(
        label='Max Items', default=1,
        validators=[validators.InputRequired()])

