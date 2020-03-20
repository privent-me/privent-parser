from pykml import parser
from lxml import etree
from datetime import datetime, timedelta
import googlemaps
import os

import db

API_key = os.environ.get('API_key')

gmaps = googlemaps.Client(key = API_key)

def load_KML(filename):
    with open(filename) as f:
        doc = parser.parse(f)
#  if you know other way to 'unobjectify' this etree, do not hesitate!
    s = etree.tostring(doc.getroot())
    return etree.fromstring(s)


def get_times(node):
# input: 'Placemark' event
    temp = node[3].text.split('from ')[1].split('.')[0]
    starting_time = int(datetime.strptime(temp, '%Y-%m-%dT%H:%M:%S').timestamp())

    temp = node[3].text.split(' to ')[1].split('.')[0]
    end_time = int(datetime.strptime(temp, '%Y-%m-%dT%H:%M:%S').timestamp())
    return(starting_time, end_time)


def get_coordinates(node):
    # TODO is it correct or should be the other way around?
    lat = float(node[4][0].text.split(',')[0])
    lon = float(node[4][0].text.split(',')[1])
    return (lat, lon)


def get_place(node):
# Need to be reverted for the purpose of googlemaps API compatibility
# (BTW: wtf? It's exported from other Google service...)
    coordinates = node[4][0].text.split(',')[1]+','+node[4][0].text.split(',')[0]
    return(gmaps.reverse_geocode(coordinates)[0]['formatted_address'])


def parse_file(filename):
    ''' parse a kml file and return a list of visits '''
    visits  = []
    doc = load_KML(filename)[0]
    for child in doc:
        if child.tag.split('}')[1] == 'Placemark':
# Searching for double space is a dirty trick, bt there is no keyword like 'visit' or 'stay;
# We need to check whether it work on files exported for other people as well
            if child[3].text.startswith('  '):
                visits.append((get_coordinates(child), get_times(child), get_place(child)))

    return visits

def parse_file_add_to_db(filename, subject_ID, info):
    conn = db.create_connection()
    visits = parse_file(filename)
    for v in visits:
        place = (v[0][0]*1e7, v[0][1]*1e7, v[2])
        place_id = db.find_place_id(conn, place)
        if place_id is None:
            place_id = db.add_place(conn, place)
        beg = v[1][0]
        end = v[1][1]
        db.add_visit(conn, (place_id, beg, end))

    conn.commit()

def parse_folder(path):
    filenames = os.listdir(path)
    subject_ID = path.split('/')[-1]
    with open(path+'/userInfo.json', 'r') as f:
        info = json.load(f)
    
    for filename in filenames:
        if not filename.startswith('userInfo'):
            parse_file_add_to_db(path+filename, subject_ID, info)



