var distanceUnits = ["blocks", "minutes", "miles", "kilometers", "feet"];
var toMilesFactors = { "blocks": 0.05, "minutes": 0.0666666667, "miles": 1.0, "kilometers": 0.621371, "feet": 0.00018939393 };

function toMiles(radius_str) {
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
    return place.name + "#" + place.geometry.location;
}
