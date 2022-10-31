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
        #return result(search.airport.data, search.d00.data, search.d01.data, search.d10.data, search.d11.data)
        return redirect("/" + str(search.airport.data) + "/" + str(search.d00.data) + "/" + str(search.d01.data) + "/" + str(search.d10.data) + "/" + str(search.d11.data))
    return render_template("index.html", form=search)

@app.route("/<airport>/<d00>/<d01>/<d10>/<d11>")
def result(airport, d00, d01, d10, d11):
    trips = ryanair.get_return_flights(str(airport), str(d00), str(d01), str(d10), str(d11))
    return render_template("show_list.html", data = trips)

if __name__ == "__main__": 
	app.run() 
