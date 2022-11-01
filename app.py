from flask import Flask, render_template, request, redirect
from forms import AirportForm
from flask_bootstrap import Bootstrap5
import requests
import json
import datetime

app = Flask(__name__, template_folder='./templates', static_folder='./static')
Bootstrap5(app)


@app.route("/", methods=['GET', 'POST'])
def hello():
    search = AirportForm(request.form)
    if request.method == 'POST':
        airport = str(search.airport.data).upper()
        d00 = search.d00.data.strftime("%d-%m-%Y")
        d01 = search.d01.data.strftime("%d-%m-%Y")
        d10 = search.d10.data.strftime("%d-%m-%Y")
        d11 = search.d11.data.strftime("%d-%m-%Y")
        return redirect("/" + airport + "/" + d00 + "/" + d01 + "/" + d10 + "/" + d11)
    return render_template("index.html", form=search)


@app.route("/<airport>/<d00>/<d01>/<d10>/<d11>")
def result(airport, d00, d01, d10, d11):

    url = "https://api.tequila.kiwi.com/v2/search"

    date_from = d00.replace("-", "/")
    date_to = d01.replace("-", "/")
    return_from = d10.replace("-", "/")
    return_to = d11.replace("-", "/")

    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': '***REMOVED***'}
    params = {'fly_from': 'city:MAD', 'date_from': date_from, 'date_to': date_to, 'return_from': return_from,
              'return_to': return_to, 'flight_type': 'round', 'nights_in_dst_from': '1', 'nights_in_dst_to': '3',
              'ret_from_diff_airport': '0', 'limit': '1000'}

    response = json.loads(requests.get(url, headers = headers, params = params).text)

    results = []
    for r in response['data']:
        results.append({"airport": r['flyTo'],
                        "city": r['cityTo'],
                        "firstDepartureTime": datetime.datetime.strptime(r['route'][0]['local_departure'],
                                                                            "%Y-%m-%dT%H:%M:%S.%fZ"),
                        "lastArrivalTime": datetime.datetime.strptime(r['route'][-1]['local_arrival'],
                                                                            "%Y-%m-%dT%H:%M:%S.%fZ"),
                        "price": round(r['price'], 2),
                        "airlines": r['airlines'],
                        "link": r['deep_link']},)

    return render_template("show_list.html", data=results)


if __name__ == "__main__":
    app.run()
