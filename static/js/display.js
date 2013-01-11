function clearMarkers() {
    for(var i=0; i<markersOnMap.length; i++) {
        markersOnMap[i].setMap(null);
    }
    placesOnMapSet = {};
    placesOnMap = [];
    markersOnMap = [];
    stopsToMarkers = {};
}

function clearPlaceList() {
    $("#placelist").text("");
}

function updateFromToStopMenus(line) {
    if(line == currentLine) {
	return;
    }
    currentLine = line;
    $.getJSON('/stops/' + $("#agency_s").val() + '/' + line + '/' + map.getCenter().lat() + '/' + map.getCenter().lng(), function(new_data) {
	console.log(new_data);
	$("#from_stop > option").remove();
	$("#to_stop > option").remove();
	for(var i = 0; i < new_data.length; i++) {
	    console.log(new_data[i]);
	    $("#from_stop").append("<option value=\"" + new_data[i]["direction_index"] + "." + new_data[i]["direction"] + "\">" + new_data[i]["stop_name"] + "</option>");
	    $("#to_stop").append("<option value=\"" + new_data[i]["direction_index"] + "." + new_data[i]["direction"] + "\">" + new_data[i]["stop_name"] + "</option>");
	}
	$("#from_stop").val($("#from_stop > option:first-child").val())
	$("#to_stop").val($("#to_stop > option:last-child").val())
    });
}

function openInfoWindowFromPlaceHash(hash) {
    openInfoWindow(placesOnMapSet[hash].info_window, placesOnMapSet[hash].marker);
}

function openInfoWindow(iw, mkr) {
    if(currentOpenInfoWindow != null) { currentOpenInfoWindow.close(); }
    currentOpenInfoWindow = iw;
    iw.open(map,mkr);
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
            stopsToMarkers[hashStop(stop)] = marker;
        }
    });
}

function displayStopsOnRouteCanvas(stops) {
    var canvasDiv = $("#lineCanvasDiv");
    var canvas = $("#lineCanvas")[0];
    console.log(canvas);
    var ctx = canvas.getContext("2d");
    ctx.fillStyle = "#993300";
    ctx.strokeStyle = "#000000";
    ctx.font = "11px sans-serif";
    ctx.textBaseline="middle";
    var vert_margin = 5;
    var horiz_margin = 10;
    var text_margin = 5;
    var stop_rad = 5;
    var stop_x = horiz_margin + stop_rad;
    var stop_y = vert_margin + stop_rad;
    var stop_height = (canvas.height - 2*stop_rad - 2*vert_margin)/(stops.length - 1);
    console.log(stops);
    for(var i=0; i<stops.length; i++) {
	console.log(stops.length, stop_rad, stop_x, stop_y, stop_height);
	var stop = stops[i];
	ctx.beginPath();
	ctx.arc(stop_x, stop_y, stop_rad, 0, 2*Math.PI);
	ctx.stroke();
	ctx.fill();
	ctx.strokeText(stop["stop_name"], stop_x + stop_rad + text_margin, stop_y);
	if(i != stops.length - 1) {
	    ctx.beginPath();
	    ctx.moveTo(stop_x, stop_y + stop_rad);
	    stop_y = stop_y + stop_height;
	    ctx.lineTo(stop_x, stop_y - stop_rad);
	    ctx.stroke();
	}
	canvasDiv.append("<a onmouseover=\"highlightStopMarker('" + hashStop(stop) + "', true);\" onmouseout=\"highlightStopMarker('" + hashStop(stop) + "', false);\">" + stop["stop_name"] + "</a><br/>");
    }
}

function highlightStopMarker(stopHash, on) {
    console.log("hover");
    var marker = stopsToMarkers[stopHash];
    if(!(typeof marker === "undefined")) {
	console.log(marker);
	if(on) {
	    marker.setIcon(colorDot("yellow"));
	} else {
	    marker.setIcon(colorDot("red"));
	}
    }
}
