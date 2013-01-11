var distanceUnits = ["miles", "kilometers", "blocks", "feet"];
var toMilesFactors = { "blocks": 0.05, "block": 0.05, "miles": 1.0, "mi": 1.0, "mile": 1.0, "kilometers": 0.621371, "kilometer": 0.621371, "km": 0.621371, "feet": 0.00018939393, "foot": 0.00018939393 };
var RADIUS_DEFAULT = 0.2;

function toMiles(radius_str) {
    if(radius_str == "") {
	return RADIUS_DEFAULT;
    }
    var radiusarr = radius_str.split(" ");
    var radius = parseFloat(radiusarr[0]);
    var unit = radiusarr[1].toLowerCase();
    console.log("Converted " + radius_str + " to " + (radius * toMilesFactors[unit]) + " miles");
    return radius * toMilesFactors[unit];
}

function colorDot(colorstr) {
    return "https://maps.gstatic.com/mapfiles/ms2/micons/" + colorstr + "-dot.png";
}

function hashPlace(place) {
    return escape(encodeURIComponent(place.name + "#" + place.geometry.location));
}

function hashStop(stop) {
    return escape(encodeURIComponent(stop.route + "#" + stop.tag));
}
