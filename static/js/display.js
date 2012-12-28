function clearMarkers() {
    for(var i=0; i<markersOnMap.length; i++) {
        markersOnMap[i].setMap(null);
    }
    placesOnMapSet = {};
    placesOnMap = [];
    markersOnMap = [];
}

function clearPlaceList() {
    $("#placelist").text("");
}

function displayPlaceList() {
    console.log("displaying place list");    
    for(var i=0; i<placesOnMap.length; i++) {
        $("#placelist").append(placesOnMap[i].name + "<br/>");
    }
}

function displayStopsOnMap(stops, colorstr) {
    var center_latlng = new google.maps.LatLng(geoloc_lat, geoloc_lng);
    console.log("original center_latlng: " + center_latlng);
    if(!(typeof map.getCenter() === "undefined")) {
	console.log("current center_latlng: " + map.getCenter());
	center_latlng = map.getCenter();
    }
    $.post('/closest_stop', {"stops": JSON.stringify(stops), "lat": center_latlng.lat(), "lon": center_latlng.lng()}, function(data) {
        data = JSON.parse(data);
        center_latlng = new google.maps.LatLng(data["lat"], data["lon"]);
        console.log("received response from closest_stop: " + center_latlng);
        var myOptions = {
            center: center_latlng,
            mapTypeControl: false,
            navigationControlOptions: {style: google.maps.NavigationControlStyle.SMALL},
            mapTypeId: google.maps.MapTypeId.ROADMAP
        };
        map.setOptions(myOptions);
	
        for(var i = 0; i < stops.length; i++) {
	    var stop = stops[i];
            var marker = new google.maps.Marker({
		position: new google.maps.LatLng(stop["lat"], stop["lon"]), 
		map: map, 
		title: stop["stop_name"],
		icon: colorDot(colorstr)
            });
            markersOnMap.push(marker);
        }
    });
}
