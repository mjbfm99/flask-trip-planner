from wtforms import Form, StringField, SelectField, DateField
from datetime import date
import datetime

class AirportForm(Form):
    next_thu = date.today() + datetime.timedelta(days=(21 + (3 - date.today().weekday()) % 7))
    airport = StringField(label="Airport ", default="MAD")
    d00 = DateField(label="between", default=next_thu)
    d01 = DateField(label = "and", default=next_thu + datetime.timedelta(days=1))
    d10 = DateField(label = "between", default=next_thu + datetime.timedelta(days=2))
    d11 = DateField(label = "and", default=next_thu + datetime.timedelta(days=3))
