#! /usr/bin/python

import urllib2
from urllib import urlencode
from xml.dom.minidom import parseString
import sqlite3
import sys

if __name__ == "__main__":
  allowed_agencies = set()
  agency_list_xml_file = urllib2.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?" + urlencode({"command": "agencyList"}))
  agency_list_xml = agency_list_xml_file.read()
  agency_list_xml_file.close()
  agency_list_dom = parseString(agency_list_xml)
  for agency_node in agency_list_dom.getElementsByTagName("agency"):
    allowed_agencies.add(agency_node.getAttribute("tag"))

  print "Connecting to DB..."
  connection = sqlite3.connect("stops.db")
  print "Connected"
  c = connection.cursor()
  for agency in sys.argv[1:]:
    if agency not in allowed_agencies:
      print "Supplied agency '" + raw_agency + "' is not an agency covered by NextBus! Continuing without processing it."
      continue
    print "Agency: " + agency
    c.execute("CREATE TABLE IF NOT EXISTS `" + agency + "` (route varchar(20), tag varchar(10), stop_name varchar(200), direction varchar(20), direction_index int(3), lat float(10,7), lon float(10,7));")
    c.execute("DELETE FROM `" + agency + "` WHERE 1;");
    route_list_xml_file = urllib2.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?" + urlencode({"command" : "routeList", "a" : agency}))
    route_list_xml = route_list_xml_file.read()
    route_list_xml_file.close()
    route_list_dom = parseString(route_list_xml)
    for route_node in route_list_dom.getElementsByTagName("route"):
      route = route_node.getAttribute("tag")
      route_name = route_node.getAttribute("title")
      print "Found route " + route_name + "(" + route + ")"
      route_xml_file = urllib2.urlopen("http://webservices.nextbus.com/service/publicXMLFeed?" + urlencode({"command" : "routeConfig", "a" : agency, "r" : route}))
      route_xml = route_xml_file.read()
      route_xml_file.close()
      route_dom = parseString(route_xml)
      stop_dict = {}
      route_xml_route_node = route_dom.getElementsByTagName("route")[0]
      for stop_node in route_xml_route_node.getElementsByTagName("stop"):
        if stop_node.parentNode == route_xml_route_node:
          stop_dict[stop_node.getAttribute("tag")] = (stop_node.getAttribute("title"), stop_node.getAttribute("lat"), stop_node.getAttribute("lon"))
      for direction in route_dom.getElementsByTagName("direction"):
        dir_tag = direction.getAttribute("tag");
        index_in_direction = 0
        for stop_node in direction.getElementsByTagName("stop"):
          stop_tag = stop_node.getAttribute("tag")
          stop = stop_dict[stop_tag]
          stop_title = stop[0]
          stop_lat = stop[1]
          stop_lon = stop[2]
          if stop_title != '':
            c.execute("INSERT INTO `" + agency + "` values (?, ?, ?, ?, ?, ?, ?);", (route, stop_tag, stop_title, dir_tag, index_in_direction, stop_lat, stop_lon));
            index_in_direction += 1
  connection.commit()
  connection.close()
        
