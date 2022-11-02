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
    airport = "MAD"


    # Approach
    #
    # 1. Search for flights to anywhere (one per city)
    # 2. Take the cities in the response
    # 3. Search for one return flight per city
    # 4. Match them and show list
    #
    # 5. Each city on the list will be clickable. After clicking a city, a new query will be made.

    # Outbound cities search (1000 cheapest flights)

    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': '***REMOVED***'}
    params = {'fly_from': airport, 'date_from': date_from, 'date_to': date_to, 'flight_type': 'oneway',
              'one_per_city': '1', 'limit': '1000'}

    response = json.loads(requests.get(url, headers=headers, params=params).text)

    # Get list of cities
    cities = []

    # Store first result for each city only
    outbound_results = []
    for r in response['data']:
        if "city:" + r['cityCodeTo'] not in cities:
            cities.append("city:" + r['cityCodeTo'])
            outbound_results.append({"outbound_airport": r['flyTo'],
                                     "city": r['cityTo'],
                                     "outbound_departure_time": datetime.datetime.strptime(r['route'][0]['local_departure'],
                                                                                      "%Y-%m-%dT%H:%M:%S.%fZ"),
                                     # "lastArrivalTime": datetime.datetime.strptime(r['route'][-1]['local_arrival'],
                                     #                                              "%Y-%m-%dT%H:%M:%S.%fZ"),
                                     "outbound_price": round(r['price'], 2),
                                     "outbound_airlines": r['airlines'],
                                     "outbound_link": r['deep_link']})

    # Get return flights
    cities_str = ','.join(cities)

    params = {'fly_from': cities_str, 'fly_to': airport, 'date_from': return_from, 'date_to': return_to,
              'flight_type': 'oneway',
              'one_per_city': '1', 'limit': '1000'}
    response = json.loads(requests.get(url, headers=headers, params=params).text)

    inbound_results = []
    dest_airports = []
    trips = []
    for r in response['data']:
        if r['flyFrom'] not in dest_airports and "city:" + r['cityCodeFrom'] in cities:
            dest_airports.append(r['flyFrom'])
            r_dict = dict(inbound_airport=r['flyFrom'], city=r['cityFrom'],
                          inbound_arrival_time=datetime.datetime.strptime(
                              r['route'][-1]['local_arrival'],
                              "%Y-%m-%dT%H:%M:%S.%fZ"), inbound_price=round(r['price'], 2),
                          inbound_airlines=r['airlines'], inbound_link=r['deep_link'])
            inbound_results.append(r_dict)
            bp = next((item for item in inbound_results if (item['city'] == r['cityFrom'] and item['inbound_price'] < r['price'])), None)
            if bp is None:
                o = next(item for item in outbound_results if item['city'] == r['cityFrom'])
                trips.append({"airport": str({r_dict['inbound_airport'], o['outbound_airport']}).replace("{", "").replace("}", "").replace("'", ""),
                              "city": r_dict['city'],
                              "departure_time": o['outbound_departure_time'],
                              "return_time": r_dict['inbound_arrival_time'],
                              "price": o['outbound_price'] + r_dict['inbound_price'],
                              "airlines": list(set(o['outbound_airlines'] + r_dict['inbound_airlines'])),
                              "item_link": "#"})

    trips = sorted(trips, key=lambda d: d['price'])

    return render_template("show_list.html", data=trips)


if __name__ == "__main__":
    app.run()
