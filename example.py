import json
from parse import parse_subject_dir
import os
from glob import glob

from colocations import subject, find_colocations
import db

def build_db(subjects):
    if os.path.exists('prevent.db'):
        os.remove('prevent.db')
    db.setup()

    for subject in subjects:
        parse_subject_dir(subject)

subjects_dirs = glob('generated_data/*')
subject_dir, infected_dir = subjects_dirs[0], subjects_dirs[1:]

print('build db')
build_db(infected_dir)

print('init subject')
subject_history = glob(subject_dir+'/*kml')
subject_id = subject_dir.split('/')[-1]
with open(subject_dir+'/subject_info.json', 'r') as f:
    info = json.load(f)
s = subject(subject_history, subject_id, info)

print('find colocations')
colocations = find_colocations(s)

print('According to our database, user ' + subject_id + ' has been colocated with COVID-positive cases in the following instances: ')
with db.create_connection() as conn:
    colocations.sort(key=lambda x: x.times[1]-x.times[0])
    for c in colocations:
        print('At ' + c.address+'   for    ', int((c.times[1]-c.times[0])/60), ' minutes')
        db.add_colocation(conn, (c.infected_id, c.subject_id, c.place_id, *c.times))
