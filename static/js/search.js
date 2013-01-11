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

function searchNearby(keyword, lat, lng, radius, colorstr, stop_num, num_stops) {
    request = {"location": new google.maps.LatLng(lat, lng), "radius": radius / toMilesFactors["kilometers"] * 1000, "keyword": keyword};
    service.nearbySearch(request, function(results, status) {
        console.log(status);        
	if(status == google.maps.places.PlacesServiceStatus.OK) {
            for (var i = 0; i < results.length; i++) {
		var place = results[i];
		var hash = hashPlace(place);
		// If this place has already been added from another stop, skip it.
		if (!(typeof placesOnMapSet[hash] === "undefined")) {
		    continue;
		}
		var marker = new google.maps.Marker({
		    position: place.geometry.location,
		    map: map,
		    title: place.name,
		    icon: colorDot(colorstr)
		});
		placesOnMapSet[hash] = {"marker": marker};
		placesOnMap.push(place);
		markersOnMap.push(marker);
		// Give a local copy of marker to avoid closure problems
		(function(mkr, pl, h) {
		    console.log(pl);
		    var desc = pl.name;
		    if(!(typeof pl.formatted_address === "undefined")) {
			desc += "<br/>" + pl.formatted_address;
		    } else if(!(typeof pl.vicinity === "undefined")) {
			desc += "<br/>" + pl.vicinity;
		    }
		    if(!(typeof pl.formatted_phone_number === "undefined")) {
			desc += "<br/>" + pl.formatted_phone_number;
		    }
		    if(!(typeof pl.url === "undefined")) {
			desc += "<br/><a href=\"" + pl.url + "\">Google Place page</a>";
		    }
		    if(!(typeof pl.website === "undefined")) {
			desc += "<br/><a href=\"" + pl.website + "\">Business website</a>";
		    }
		    if(!(typeof pl.rating === "undefined")) {
			desc += "<br/>Rating: " + pl.rating;
		    }
		    var infoWindow = new google.maps.InfoWindow({
			content: desc
		    });
		    placesOnMapSet[h]["info_window"] = infoWindow;
		    google.maps.event.addListener(mkr, 'click', function() {
			openInfoWindow(infoWindow, mkr);
		    });
		    var placeEntry = "<a href=\"#\" onclick=\"openInfoWindowFromPlaceHash('" + hashPlace(pl) + "')\">" + pl.name + "</a>";
		    if(!(typeof pl.rating === "undefined")) {
			placeEntry += "<span class=\"place_list_rating\">" + pl.rating + "</span>";
		    }
		    $("#placelist").append(placeEntry + "<br/>");
		})(marker, place, hash);
            }
        }
	searchProgress = searchProgress + Math.floor(100/num_stops) + (100 % num_stops > stop_num ? 1 : 0);
	$("#search_progress").css("width", searchProgress + "%");	
	//if(stop_num == num_stops - 1) {
	// if JS can interleave calls to this function(results, status), this is a race condition; otherwise ok
	if(searchProgress == 100) {
	    $("button#search").button("reset");
	    $("#search_progress_outer").css("display", "none");
	    $("div#numresults").text((placesOnMap.length > 0 ? placesOnMap.length : "No") + " results");
	}
    });
}
