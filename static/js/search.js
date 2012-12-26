function getRoutesForAgency(agency) {
    var routes = new Array();
    $.getJSON('/routes/' + agency, function(data) {
        routes = data;
    });
    $( "#line" ).autocomplete('option', 'source', function(req, responseFn) {
        var re = $.ui.autocomplete.escapeRegex(req.term);
        var matcher = new RegExp( "^" + re, "i" );
        var a = $.grep( routes, function(item,index){
            return matcher.test(item);
        });
        responseFn( a );
    });
}

function searchNearby(keyword, lat, lng, radius, colorstr) {
    request = {"location": new google.maps.LatLng(lat, lng), "radius": radius / toMilesFactors["kilometers"] * 1000, "keyword": keyword};
    service.nearbySearch(request, function(results, status) {
        console.log(status);        
	if(status == google.maps.places.PlacesServiceStatus.OK) {
            for (var i = 0; i < results.length; i++) {
		var place = results[i];
		var hash = hashPlace(place);
		// If this place has already been added from another stop, skip it.
		if (!(typeof placesOnMap[hash] === "undefined")) {
		    continue;
		}
		var marker = new google.maps.Marker({
		    position: place.geometry.location,
		    map: map,
		    title: place.name,
		    icon: colorDot(colorstr)
		});
		placesOnMap[hash] = place;
		markersOnMap.push(marker);
		// Give a local copy of marker to avoid closure problems
		(function(mkr) {
		    var infoWindow = new google.maps.InfoWindow({
			content: place.name + "<br>" + place.geometry.location
		    });		    
		    google.maps.event.addListener(marker, 'click', function() {
			if(openInfoWindow != null) { openInfoWindow.close(); }
			openInfoWindow = infoWindow;
			infoWindow.open(map,mkr);
		    });
		})(marker);
            }
        }
    });
}
