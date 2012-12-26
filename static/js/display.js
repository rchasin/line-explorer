function clearMarkers() {
    for(var i=0; i<markersOnMap.length; i++) {
        markersOnMap[i].setMap(null);
    }
    placesOnMap = [];
    markersOnMap = [];
}

function clearPlaceList() {
    $("#placelist").text("");
}

function displayPlaceList() {
    console.log("displaying place list");    
    for(hash in placesOnMap) {
        $("#placelist").append(placesOnMap[hash].name + "<br/>");
    }
}

function displayStopsOnMap(stops, colorstr) {
    var center_latlng = new google.maps.LatLng(geoloc_lat, geoloc_lng);
    console.log("original center_latlng: " + center_latlng);
    $.post('/closest_stop', {"stops": JSON.stringify(stops), "lat": geoloc_lat, "lon": geoloc_lng}, function(data) {
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
