from flask import Flask, request, render_template, jsonify, url_for, redirect
from geopy import Point
from geopy import distance as geopydistance
import sqlite3, json, sys, urllib2
from xml.dom.minidom import parseString

app = Flask(__name__, template_folder='static/template')

@app.route('/')
def index():
    allowed_agencies = {}
    agency_list_xml_file = urllib2.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList")
    agency_list_xml = agency_list_xml_file.read()
    agency_list_xml_file.close()
    agency_list_dom = parseString(agency_list_xml)
    for agency_node in agency_list_dom.getElementsByTagName("agency"):
        allowed_agencies[agency_node.getAttribute("tag")] = (agency_node.getAttribute("regionTitle"), agency_node.getAttribute("title"))
#    return render_template('index.html', agencies=allowed_agencies)
#    return render_template('index.html')

# render index.html statically so we can use angular templates with {{}}
# we don't actually need templates since we're using this as an api
    return app.send_static_file('index.html')

# I have no idea what to do with this angular ui bootstrap typeahead directive
@app.route('/template/<path:filename>')
def custom_static(filename):
    return redirect(url_for('static', filename='template/' + filename))

@app.route('/api/agencies')
def all_agencies():
    agency_list_xml_file = urllib2.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList")
    agency_list_xml = agency_list_xml_file.read()
    agency_list_xml_file.close()
    agency_list_dom = parseString(agency_list_xml)
    agencies = [
        {'id': agency_node.getAttribute('tag'),
         'name': agency_node.getAttribute('title')}
        for agency_node in agency_list_dom.getElementsByTagName("agency")
    ]
    return jsonify(agencies=agencies)

@app.route('/api/lines/<agencyId>')
def routesForAgency(agencyId):
    conn = connect_to_stops()
    c = conn.cursor()
    c.execute('select distinct route from `' + scrub(agencyId) + '`')
    lines = [{'id': ln[0], 'name': ln[0]} for ln in c]
    return jsonify(lines=lines)

def allstops(agency, route):
    sys.stderr.write("route: " + route + "\n")
    conn = connect_to_stops()
    c = conn.cursor()
    c.execute('select * from `' + scrub(agency) + '` where route=?', [route])
    dl=[]
    for row in c:
        d = {}
        for (col,val) in zip(c.description,row):
            d[col[0]] = val
        dl.append(d)
    return json.dumps(dl)

# TODO: DO NOT pass lat and lon in the request URL, that is horrible for any semblance of privacy
# (if we send them over POST, we could at least potentially encrypt them)
@app.route('/stops/<agency>/<path:route>/<current_lat>/<current_lon>')
def stops(agency, route, current_lat, current_lon):
    stops = json.loads(allstops(agency, route))
    directions = sorted(list(set([s['direction'] for s in stops])))
    closest_stop_in_direction = {}
    for direction in directions:
        closest_stop_in_direction[direction] = closest_stop([s for s in stops if s['direction'] == direction], current_lat, current_lon)
    limited_stops = [s for s in stops if s['direction_index'] >= closest_stop_in_direction[s['direction']]['direction_index']]
    sorted_limited_stops = []
    direction_index_start_zero = False
    for direction in directions: # badly defined for len(directions) > 2
        sorted_in_direction = sorted([s for s in limited_stops if s['direction'] == direction], lambda x,y: (1 if direction_index_start_zero else -1)*(x['direction_index'] - y['direction_index']))
        sorted_limited_stops += sorted_in_direction
        direction_index_start_zero = True
    sys.stderr.write(str(sorted_limited_stops) + "\n")
    return json.dumps(sorted_limited_stops)

# from_stop and to_stop are in the form: direction_index.direction
@app.route('/min_stops/<agency>/<path:route>/<radius>/<current_lat>/<current_lon>/<from_stop>/<to_stop>')
#@app.route('/min_stops', methods=['POST'])
def min_stops(agency, route, radius, current_lat, current_lon, from_stop, to_stop):
    limited_stops = json.loads(stops(agency, route, current_lat, current_lon))
    narrowed_limited_stops = stops_between(limited_stops, from_stop, to_stop)
    sys.stderr.write("NLS: " + str(narrowed_limited_stops) + "\n")
    ms = min_stops(narrowed_limited_stops, radius)
    # sort by distance from current_lat, current_lon
    current_latlon = {"lat": current_lat, "lon": current_lon}
    ms = sorted(ms, lambda s,t: 1 if stop_distance(s, current_latlon) > stop_distance(t, current_latlon) else -1)
    return json.dumps(ms)

# INTERNAL Given a list of stops and two boundary stops (as
# direction_index.direction), returns a sublist consisting of the
# boundary stops and all stops between them.
def stops_between(stops, b1, b2):
    bdi1 = int(b1[:b1.find(".")])
    bd1 = b1[b1.find(".") + 1:]
    bdi2 = int(b2[:b2.find(".")])
    bd2 = b2[b2.find(".") + 1:]
    # Different directions means we must be considering ourselves
    # between the stops already so they will be upper bounds on the
    # stops we want
    if bd1 != bd2:
        return [s for s in stops if (s["direction"] == bd1 and s["direction_index"] <= bdi1) or (s["direction"] == bd2 and s["direction_index"] <= bdi2)]
    # Same direction means we are off to one side of them so they will be monotonic
    else:
        return [s for s in stops if (s["direction"] == bd1 and s["direction_index"] >= min(bdi1, bdi2) and s["direction_index"] <= max(bdi1, bdi2))]

# INTERNAL Given a list of stops and a radius, returns a sublist consisting of the endpoints and of
# stops whose elements are at least radius apart if they are stops for the same direction.
def min_stops(stops, radius):
    radius = float(radius)
    ms = []
    directions = set([s['direction'] for s in stops])
    endpoints = {}
    # For each direction, add the endpoint in this stop list (i.e. the one the user would be
    # traveling to) and continue along the route towards the user, adding a stop only if the
    # distance from the previously added stop is larger than radius (i.e. be greedy). Also add the
    # other "endpoint" (i.e. the stop closest to the user).
    for d in directions:
        dstops = [s for s in stops if s['direction'] == d]
        dstops = sorted(dstops, lambda s,t: s['direction_index'] - t['direction_index'])
        (endpoint, step) = (dstops[0], 1) if dstops[0]['direction_index'] == 0 else (dstops[-1], -1)
        # start_index should be the index after/before endpoint, not equal to endpoint
        (start_index, end_index) = (1, len(dstops)) if step == 1 else (len(dstops) - 2, -1)
        ms.append(endpoint)
        # Assume the stops on the route form the shortest path from a stop to a later stop, that is,
        # dist(s,s+i) = dist(s,s+j) + dist(s+j,s+i) for 0 < j < i. Thus we can keep track of a
        # cumulative distance since the last stop we added and add a new stop when that would be too
        # large.
        last_added_stop = endpoint
        last_seen_stop = endpoint
        distance_since_last_added_stop = 0
        for index in range(start_index, end_index, step):
            current_stop = dstops[index]
            delta_distance = stop_distance(current_stop, last_seen_stop)
#            sys.stderr.write(str(index) + ", DELTA_DIST: " + str(delta_distance) + " [(" + str(current_stop['lat']) + "," + str(current_stop['lon']) + ") -> (" + str(last_seen_stop['lat']) + "," + str(last_seen_stop['lon']) + ")], radius: " + str(radius) + "\n")
            distance_since_last_added_stop += delta_distance
            # If we have moved too far from the last added stop, add the last seen stop and reset
            # distances accordingly.
            if distance_since_last_added_stop > radius:
                # This if takes care of the case where we already added the last_seen_stop due to
                # the if clause for delta_distance > radius firing. We don't want to add it
                # again. Note that being in the distance-too-large if clause in this situation means
                # delta_distance is again > radius so the second clause will fire and current_stop
                # will get added.
                if last_added_stop != last_seen_stop:
                    ms.append(last_seen_stop)
                    last_added_stop = last_seen_stop
                distance_since_last_added_stop = delta_distance
                # It's possible that delta_distance is large enough in itself to make the current
                # stop be added. But we only need to check /again/ if we added the previous stop, in
                # which case we normally wouldn't add this one.
                if distance_since_last_added_stop > radius: # i.e. delta_distance > radius
                    ms.append(current_stop)
                    last_added_stop = current_stop
                    distance_since_last_added_stop = 0
            last_seen_stop = current_stop
        if last_added_stop != last_seen_stop:
            ms.append(last_seen_stop)
    return ms

@app.route('/closest_stop', methods=['POST'])
def closest_stop():
    if 'stops' not in request.form or 'lat' not in request.form or 'lon' not in request.form:
        sys.stderr.write("stops or lat or lon not in the form: " + str(request.form) + "\n")
        return ""
    stops = json.loads(request.form['stops'])
    min_stop = closest_stop(stops, request.form['lat'], request.form['lon'])
    return json.dumps(min_stop)

# INTERNAL
def closest_stop(stops, current_lat, current_lon):
    min_dist = -1
    min_stop = None
    for stop in stops:
        dist = distance(Point(stop['lat'], stop['lon']), Point(current_lat, current_lon))
        if dist < min_dist or min_stop == None:
            min_dist = dist
            min_stop = stop
    return min_stop

# INTERNAL
# Distance between two stops (in whatever unit is returned by distance(p1,p2))
def stop_distance(s1, s2):
    return distance(Point(s1['lat'], s1['lon']), Point(s2['lat'], s2['lon']))

# Distance in miles between two coordinates.
def distance(p1, p2):
    return geopydistance.distance(p1, p2).miles


@app.route('/routes/<agency>')
def routes(agency):
    conn = connect_to_stops()
    c = conn.cursor()
    c.execute('select distinct route from `' + scrub(agency) + '`')
    try:
        l = sorted([int(x[0]) for x in c])
    except ValueError:  # Some route is not an integer
        l = sorted([x[0] for x in c])
    return json.dumps(l)


# Annoying hack to clean 'agency' because sqlite won't let you have variable table names
# with ? in execute. It would be best to check against the agency database but that's kind of a lot of work and this is just as safe and works just as well because right now those agencies have only alphanumeric chars and hyphens
def scrub(table_name):
    return ''.join(c for c in table_name if c.isalnum() or c == '-')        

def connect_to_stops():
    return sqlite3.connect("stops.db")

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
