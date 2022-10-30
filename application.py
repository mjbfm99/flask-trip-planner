from flask import Flask, render_template, request, redirect 
from markupsafe import escape
from forms import AirportForm
from ryanair import Ryanair
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
ryanair = Ryanair("EUR")
Bootstrap5(app)

@app.route("/", methods=['GET', 'POST'])
def hello():    
    search = AirportForm(request.form)
    if request.method == 'POST':
        return result(search.airport, search.d00, search.d01, search.d10, search.d11)
    return render_template("index.html", form=search)

@app.route("/<airport>/<d00>/<d01>/<d10>/<d11>") 
def result(airport, d00, d01, d10, d11):
    trips = ryanair.get_return_flights(airport.data, str(d00.data), str(d01.data), str(d10.data), str(d11.data))
    return render_template("show_list.html", data = trips)

if __name__ == "__main__": 
	app.run() 
