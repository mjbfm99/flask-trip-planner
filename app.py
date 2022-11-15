# pylint: disable=line-too-long
import os

import flask_bootstrap
import requests
import json
import datetime
import forms
from flask import Flask, render_template, request, redirect
import csv


app = Flask(__name__, template_folder='./templates', static_folder='./static')
flask_bootstrap.Bootstrap5(app)
kiwi_key = os.environ['KIWI_API_KEY']


@app.route("/", methods=['GET', 'POST'])
def hello():
    search = forms.AirportForm(request.form)
    if request.method == 'POST':
        print(request)
        print(request.form)
        airport = request.form['autocomplete']
        d00 = search.d00.data.strftime("%d-%m-%Y")
        d01 = search.d01.data.strftime("%d-%m-%Y")
        d10 = search.d10.data.strftime("%d-%m-%Y")
        d11 = search.d11.data.strftime("%d-%m-%Y")
        return redirect("/".join(["/explore", airport, d00, d01, d10, d11]))
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

        cities_csv = csv.reader(open("cities.csv"), delimiter=",")

        searchTextList = []
        # for row in airports_csv:
        #     searchTextList.append([str(row[0]) + " - " + str(row [2]), str(row[0])])

        for row in cities_csv:
            searchTextList.append([row[1] + " - " + row[0], row[0]])
        return render_template("start.html", form=search, cities=searchTextList[1:])


@app.route("/explore/<airport>/<d00>/<d01>/<d10>/<d11>")
def explore_result(airport, d00, d01, d10, d11):
    url = "https://api.tequila.kiwi.com/v2/search"

    date_from = d00.replace("-", "/")
    date_to = d01.replace("-", "/")
    return_from = d10.replace("-", "/")
    return_to = d11.replace("-", "/")
    #airport = "MAD"

    # Approach
    #
    # 1. Search for flights to anywhere (one per city)
    # 2. Take the cities in the response
    # 3. Search for one return flight per city
    # 4. Match them and show list
    #
    # 5. Each city on the list will be clickable. After clicking a city, a new query will be made.

    # Outbound cities search (1000 cheapest flights)

    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': kiwi_key}
    params = {'fly_from': airport, 'date_from': date_from, 'date_to': date_to, 'flight_type': 'oneway',
              'one_per_city': '1', 'limit': '500'}

    response = json.loads(requests.get(url, headers=headers, params=params).text)
    #print(response)


    # Get list of cities
    cities = []

    # Store first result for each city only
    outbound_results = []
    for r in response['data']:
        if "city:" + r['cityCodeTo'] not in cities:
            cities.append("city:" + r['cityCodeTo'])
            outbound_results.append({"outbound_airport": r['flyTo'],
                                     "city": r['cityTo'],
                                     "outbound_departure_time": datetime.datetime.strptime(
                                         r['route'][0]['local_departure'],
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
            bp = next((item for item in inbound_results if
                       (item['city'] == r['cityFrom'] and item['inbound_price'] < r['price'])), None)
            if bp is None:
                o = next(item for item in outbound_results if item['city'] == r['cityFrom'])
                trips.append({"airport": str({r_dict['inbound_airport'], o['outbound_airport']}).replace("{",
                                                                                                         "").replace(
                    "}", "").replace("'", ""),
                              "city": r_dict['city'],
                              "departure_time": o['outbound_departure_time'],
                              "return_time": r_dict['inbound_arrival_time'],
                              "price": o['outbound_price'] + r_dict['inbound_price'],
                              "airlines": list(set(o['outbound_airlines'] + r_dict['inbound_airlines'])),
                              "link": "/".join(["/round", airport, r['cityCodeFrom'], d00, d01, d10, d11])
                              })

    trips = sorted(trips, key=lambda d: d['price'])

    return render_template("show_explore.html", data=trips, airport=airport)


@app.route("/round/<origin>/<destination>/<d00>/<d01>/<d10>/<d11>")
def round_result(origin, destination, d00, d01, d10, d11):
    date_from = d00.replace("-", "/")
    date_to = d01.replace("-", "/")
    return_from = d10.replace("-", "/")
    return_to = d11.replace("-", "/")

    headers = {'Content-Type': 'application/json; charset=utf/8', 'apikey': kiwi_key}
    params = {'fly_from': origin, 'fly_to': destination, 'date_from': date_from, 'date_to': date_to,
              'return_from': return_from, 'return_to': return_to, 'flight_type': 'round',
              'limit': '100'}

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
