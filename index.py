from flask import Flask, request, render_template
from geopy import Point
from geopy import distance as geopydistance
import sqlite3, json, sys

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def allstops(agency, route):
    sys.stderr.write("route: " + route + "\n")
    conn = connect_to_stops()
    c = conn.cursor()
    c.execute('select * from ' + scrub(agency) + ' where route=?', [route])
    dl=[]
    for row in c:
        d = {}
        for (col,val) in zip(c.description,row):
            d[col[0]] = val
        dl.append(d)
    return json.dumps(dl)

# TODO: DO NOT pass lat and lon in the request URL, that is horrible for any semblance of privacy
# (if we send them over POST, we could at least potentially encrypt them)
@app.route('/stops/<agency>/<route>/<current_lat>/<current_lon>')
def stops(agency, route, current_lat, current_lon):
    stops = json.loads(allstops(agency, route))
    directions = list(set([s['direction'] for s in stops]))
    closest_stop_in_direction = {}
    for direction in directions:
        closest_stop_in_direction[direction] = closest_stop([s for s in stops if s['direction'] == direction], current_lat, current_lon)
    limited_stops = [s for s in stops if s['direction_index'] >= closest_stop_in_direction[s['direction']]['direction_index']]
    return json.dumps(limited_stops)

@app.route('/min_stops/<agency>/<route>/<radius>/<current_lat>/<current_lon>')
#@app.route('/min_stops', methods=['POST'])
def min_stops(agency, route, radius, current_lat, current_lon):
    limited_stops = json.loads(stops(agency, route, current_lat, current_lon))
    ms = min_stops(limited_stops, radius)
    return json.dumps(ms)

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
    sys.stderr.write("there are stops\n" + str(request.form)  + "\n")
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
    c.execute('select distinct route from ' + scrub(agency))
    try:
        l = sorted([int(x[0]) for x in c])
    except ValueError:  # Some route is not an integer
        l = sorted([x[0] for x in c])
    return json.dumps(l)


# Annoying hack to clean 'agency' because sqlite won't let you have variable table names
# with ? in execute
def scrub(table_name):
    return ''.join(c for c in table_name if c.isalnum())        

def connect_to_stops():
    return sqlite3.connect("stops.db")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
