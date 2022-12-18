# pylint: disable=line-too-long
import os

import flask_bootstrap
import requests
import json
import datetime
import forms
from flask import Flask, render_template, request, redirect, url_for
import csv
import base64

app = Flask(__name__, template_folder='./templates', static_folder='./static')
flask_bootstrap.Bootstrap5(app)
kiwi_key = os.environ['KIWI_API_KEY']


@app.route("/", methods=['GET', 'POST'])
def hello():
    search = forms.AirportForm(request.form)
    if request.method == 'POST':
        url = "/"
        print(request.form)

        if request.form['search'] == "explore":
            date_from = request.form['date0']
            date_to = request.form['date1']
            origin = request.form['origin']
            nights_from = request.form['days0']
            nights_to = request.form['days1']
            search_id = base64.b64encode(str([origin, date_from, date_to, nights_from, nights_to]).encode("ascii")).decode("utf-8").replace("=", "")
            url = "/".join(["/explore", search_id])

        elif request.form['search'] == "round":
            date_from = request.form['date0']
            date_to = request.form['date1']
            origin = request.form['origin']
            destination = request.form['destination']
            nights_from = request.form['days0']
            nights_to = request.form['days1']
            search_id = base64.b64encode(str([origin, destination, date_from, date_to, nights_from, nights_to]).encode("ascii")).decode("utf-8").replace("=", "")
            url = "/".join(["/round", search_id])

        elif request.form['search'] == "oneway":
            pass
        elif request.form['search'] == "multi":
            pass
        else:
            pass
        #return redirect("/".join(["/explore", airport, d00, d01, d10, d11]))
        return redirect(url)
    else:
        # airports_csv = csv.reader(open("airports.csv", "r"), delimiter=",")
        # 0. Code
        # 1. Time zone
        # 2. Name
        # 3. City code
        # 4. Country ID
        # 5. Location
        # 6. Elevation
        # 7. URL
        # 8. ICAO
        # 9. City
        # 10. County
        # 11. State

        next_thu = datetime.date.today() + datetime.timedelta(days=(21 + (3 - datetime.date.today().weekday()) % 7))
        default_dates = [next_thu.strftime("%Y-%m-%d"),
                         (next_thu + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                         (next_thu + datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
                         (next_thu + datetime.timedelta(days=3)).strftime("%Y-%m-%d")]

        cities_csv = csv.reader(open("cities.csv"), delimiter=",")

        searchTextList = []
        # for row in airports_csv:
        #     searchTextList.append([str(row[0]) + " - " + str(row [2]), str(row[0])])

        for row in cities_csv:
            searchTextList.append([row[1] + " - " + row[0], row[0]])
        return render_template("start.html", form=search, cities=searchTextList[1:], default_dates=default_dates)


@app.route("/explore/<search_id>")
def explore_result(search_id):

    params = base64.b64decode(search_id + '=' * (-len(search_id) % 4)).decode("utf-8")[1:-1].replace("'", "").split(", ")

    [airport, date_from, date_to, nights_from, nights_to] = params
    return_from = date_from
    return_to = date_to

    url = "https://api.tequila.kiwi.com/v2/search"
    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': kiwi_key}
    params = {'fly_from': airport, 'date_from': date_from, 'date_to': date_to, 'flight_type': 'round',
              'return_from': return_from, 'return_to': return_to, 'one_for_city': '1', 'ret_from_diff_city': '0',
              'sort': 'price', 'nights_in_dst_from': nights_from, 'nights_in_dst_to': nights_to, 'limit': '100'}

    response = json.loads(requests.get(url, headers=headers, params=params).text)

    trips = []

    for r in response['data']:
        trips.append({"city": r['cityTo'],
                      "price": r['price'],
                      "link": "/".join(["/round", base64.b64encode(str([airport, "city:" + r['cityCodeTo'], date_from, date_to, nights_from, nights_to]).encode("ascii")).decode("utf-8").replace("=", "")])})

    return render_template("show_explore.html", data=trips, airport=airport)


@app.route("/round/<search_id>")
def round_result(search_id):
    params = base64.b64decode(search_id + '=' * (-len(search_id) % 4)).decode("utf-8")[1:-1].replace("'", "").split(", ")

    [origin, destination, date_from, date_to, nights_from, nights_to] = params
    return_from = date_from
    return_to = date_to

    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': kiwi_key}
    params = {'fly_from': origin, 'fly_to': destination, 'date_from': date_from, 'date_to': date_to,
              'return_from': return_from, 'return_to': return_to, 'flight_type': 'round',
              'limit': '100', 'nights_in_dst_from': nights_from, 'nights_in_dst_to': nights_to}

    url = "https://api.tequila.kiwi.com/v2/search"
    response = json.loads(requests.get(url, headers=headers, params=params).text)

    # Concept:
    # In header, a description of the selected itinerary and date range
    # In the list, each leg of the trip with:
    # - Origin -> Destination Airports
    # - Departure and arrival time and date
    # - Number of stops
    # - Airlines
    # - Duration
    # Each trip with:
    # - Price
    # - Link

    trips = []

    for r in response['data']:

        arrival_at_index = 0
        airlines = []
        airlines_iata = []

        carriers_json = json.load(open("carriers.json"))

        for leg in enumerate(r['route']):
            airlines_iata.append(leg[1]['airline'])
            carrier_name = next((item['name'] for item in carriers_json if item['id'] == leg[1]['airline']), leg[1]['airline'])
            airlines.append(carrier_name)
            if leg[1]['flyTo'] == r['flyTo']:
                arrival_at_index = leg[0]


        outbound_route = r['route'][:arrival_at_index + 1]
        inbound_route = r['route'][arrival_at_index + 1:]

        outbound_departure_time = datetime.datetime.strptime(r['local_departure'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
        outbound_arrival_time = datetime.datetime.strptime(r['local_arrival'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
        outbound_departure_date = datetime.datetime.strptime(r['local_departure'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a %b %d")
        outbound_arrival_date = datetime.datetime.strptime(r['local_arrival'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a %b %d")

        inbound_departure_time = datetime.datetime.strptime(inbound_route[0]['local_departure'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
        inbound_arrival_time = datetime.datetime.strptime(inbound_route[-1]['local_arrival'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M")
        inbound_departure_date = datetime.datetime.strptime(inbound_route[0]['local_departure'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a %b %d")
        inbound_arrival_date = datetime.datetime.strptime(inbound_route[-1]['local_arrival'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a %b %d")

        if arrival_at_index == 0:
            outbound_stops_str = "Direct"
        else:
            outbound_stops_str = str(arrival_at_index) + " stops"

        if arrival_at_index + 2 == len(r['route']):
            inbound_stops_str = "Direct"
        else:
            inbound_stops_str = str(len(r['route']) - 2 - arrival_at_index) + " stops"

        trips.append({'price': r['price'],
                      'link': r['deep_link'],
                      'outbound_route': outbound_route,
                      'outbound_origin_airport': r['flyFrom'],
                      'outbound_destination_airport': r['flyTo'],
                      'outbound_airlines': ", ".join(airlines[:arrival_at_index + 1]),
                      'outbound_airlines_iata': list(dict.fromkeys(airlines_iata[:arrival_at_index + 1])),
                      'outbound_departure_time': outbound_departure_time,
                      'outbound_arrival_time': outbound_arrival_time,
                      'outbound_stops_str': outbound_stops_str,
                      'outbound_duration': str(r['duration']['departure'] // 3600) + "h" + str((r['duration']['departure'] // 60) % 60) + "m",
                      'outbound_departure_date': outbound_departure_date,
                      'outbound_arrival_date': outbound_arrival_date,
                      'inbound_route': inbound_route,
                      'inbound_origin_airport': inbound_route[0]['flyFrom'],
                      'inbound_destination_airport': inbound_route[-1]['flyTo'],
                      'inbound_airlines': ", ".join(airlines[arrival_at_index + 1:]),
                      'inbound_airlines_iata': list(dict.fromkeys(airlines_iata[arrival_at_index + 1:])),
                      'inbound_departure_time': inbound_departure_time,
                      'inbound_arrival_time': inbound_arrival_time,
                      'inbound_stops_str': inbound_stops_str,
                      'inbound_duration': str(r['duration']['return']//3600) + "h" + str((r['duration']['return']//60)%60) + "m",
                      'inbound_departure_date': inbound_departure_date,
                      'inbound_arrival_date': inbound_arrival_date,
                      'price': r['price'],
                      'link': r['deep_link']
                      })

    # duration fields:
    # duration['departure']: outbound duration
    # duration['return']: inbound duration

    # route (outbound_route or inbound_route) fields:
    # route[i]['flyTo']: destination airports
    # route[i]['flyFrom']: origin airports
    # route[i]['local_departure']: departure times
    # route[i]['local_arrival]': arrival times
    # route[i]['airline']: airlines
    # route[arrival_at_route_index]: number of stops

    return render_template("show_round.html", data=trips)


if __name__ == "__main__":
    app.run()
