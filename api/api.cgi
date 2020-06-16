#!/usr/bin/python3

import cgi
import configparser
import csv
import json
import os
import sys

ggetc = "/var/www/guidgrabber/etc"
available_guids_cols = [
    "guid", "appid", "servicetype", "sandboxzone",
    "kubeadmin", "redirecturl"
]
ggconfig = configparser.ConfigParser()
ggconfig.read(ggetc + '/gg.cfg')

def abort_bad_request(msg=None):
    print("Status: 400 Bad Request\n")
    if msg:
        print(msg)
    sys.exit(0)

def abort_forbidden(msg=None):
    print("Status: 403 Forbidden\n")
    if msg:
        print(msg)
    sys.exit(0)

def abort_not_found(msg=None):
    print("Status: 404 Not Found\n")
    if msg:
        print(msg)
    sys.exit(0)

def send_response_data(data):
    print("Content-type: application/json\n")
    print(json.dumps(data))
    sys.exit(0)

def get_labconfig(owner, code):
    labconfig_csv = os.path.join(ggetc, owner, 'labconfig.csv')
    try:
        with open(labconfig_csv, encoding='utf-8') as labconfig:
            reader = csv.DictReader(labconfig)
            for row in reader:
                if row.get('code') == code:
                    return row
            abort_not_found()
    except FileNotFoundError:
        abort_not_found()

def read_available_guids_cols(available_guids_csv):
    try:
        with open(available_guids_csv, encoding='utf-8') as available_guids:
            return csv.reader(available_guids).__next__()
    except (FileNotFoundError, StopIteration):
        return None


def handle_post_lab_guid(owner, code, guid, data):
    labconfig = get_labconfig(owner, code)
    if labconfig['servicetype'] == 'agnosticd-bookbag':
        handle_post_agnosticd_bookbag_lab_guid(labconfig, owner, code, guid, data)
    else:
        abort_bad_request('servicetype {} cannot use api'.format(labconfig['servicetype']))

def handle_post_agnosticd_bookbag_lab_guid(labconfig, owner, code, guid, data):
    if 'bookbag_url' not in data:
        abort_bad_request('bookbag_url must be provided')
    write_available_lab_guid(labconfig, owner, code, guid, data)
    send_response_data({"ok": True})

def write_available_lab_guid(labconfig, owner, code, guid, data):
    available_guids_csv = os.path.join(ggetc, owner, 'availableguids-{}.csv'.format(code))
    csv_available_guids_cols = read_available_guids_cols(available_guids_csv)

    available_guids_csv_writer = csv.writer(open(available_guids_csv, 'a'), delimiter=',')

    if csv_available_guids_cols:
        if set(available_guids_cols) != set(csv_available_guids_cols):
            abort_bad_request('Columns in available guids CSV does not match expected format.')
    else:
        available_guids_csv_writer.writerow(available_guids_cols)

    available_guids_csv_writer.writerow([
        guid,
        '', # appid
        labconfig['servicetype'],
        '', # sandboxzone
        '', # kubeadmin
        data.get('bookbag_url', '')
    ])


# API calls must authenticate with a Bearer token
auth_header = os.environ.get('HTTP_AUTHORIZATION')
if not auth_header \
or not auth_header.startswith('Bearer ') \
or not auth_header[7:] == ggconfig.get('api', 'token'):
    abort_forbidden()

api_path = os.environ.get('PATH_INFO')
if api_path:
    api_path = api_path.split('/')
    api_path.pop(0)
else:
    abort_not_found()

api_method = os.environ.get('REQUEST_METHOD')

api_data = None
if api_method in ('POST', 'PUT'):
    try:
        api_data = json.loads(sys.stdin.read())
        if 'data' in api_data:
            api_data = api_data['data']
    except:
        abort_bad_request()
        sys.exit(0)

# /lab/<labconfig>/<code>/guid
if len(api_path) == 4 \
and api_path[0] == 'lab' \
and api_method == 'POST':
    handle_post_lab_guid(api_path[1], api_path[2], api_path[3], api_data)
else:
    abort_not_found()

sys.exit(0)
