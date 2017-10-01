from wtforms import Form, FloatField, validators

class InputForm(Form):
    A = FloatField(
        label='Backtest Parameter', default=100,
        validators=[validators.InputRequired()])

