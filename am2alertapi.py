#!/usr/bin/env python3
#
# API adapter from Prometheus Alertmanager to UW AlertAPI
#   ssh://git@git.s.uw.edu/ue/monitoring.git

# All options via environment variables
#  ALERTAPI_TOKEN - token for AlertAPI access
#  ALERTAPI_ENDPOINT - full URL for AlertAPI
#  ALERT_ORGANIZATION - Service Now Organization Name
#  BIND_ADDR - Optional. 0.0.0.0 is default 

import json
import requests
import socket
import time
import random
import os
import sys
import signal
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer

# unbuffer stdout for timely logs
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

# Some logging systems like stackdriver distinguish between stdout and stderr
def loginfo(msg):
    sys.stdout.write('am2alertapi info: {0}\n'.format(msg))

def logerror(msg):
    sys.stderr.write('am2alertapi error: {0}\n'.format(msg))

def cleanexit(signum, frame):
    loginfo('shutting down')
    sys.exit()

signal.signal(signal.SIGTERM, cleanexit)
signal.signal(signal.SIGINT, cleanexit)

# this determines the Focus to AlertAPI urgency mapping
focus_2_urgency = {1: 1, 2: 1, 3: 2, 4: 3}

if not 'ALERTAPI_TOKEN' in os.environ:
    logerror('environment ALERTAPI_TOKEN not set')
    sys.exit(1)

if not 'ALERTAPI_ENDPOINT' in os.environ:
    logerror('environment ALERTAPI_ENDPOINT not set')
    sys.exit(1)

if not 'ALERT_ORGANIZATION' in os.environ:
    logerror('environment ALERT_ORGANIZATION not set')
    sys.exit(1)

token = os.environ['ALERTAPI_TOKEN']
endpoint = os.environ['ALERTAPI_ENDPOINT']
ci_organization = os.environ['ALERT_ORGANIZATION']
bindto = ''
if 'BIND_ADDR' in os.environ:
    bindto = os.environ['BIND_ADDR']

def translate(amalert):
    results = []
    for alert in amalert['alerts']:
        result = {}
        result['ci'] = {}
        result['component'] = {}
        result['message'] = ''
        
        # If labels.ci_name not specified ci.name is hostname
        if alert['labels'].get('hostname'):
            result['ci']['name'] = alert['labels']['hostname']
        if alert['labels'].get('ci_name'):
            result['ci']['name'] = alert['labels']['ci_name']
        if alert['labels'].get('ci_sysid'):
            result['ci']['sysid'] = alert['labels']['ci_sysid']
        result['ci']['organization'] = ci_organization

        result['component']['name'] = alert['labels']['alertname']
        result['title'] = alert['annotations']['summary']
        prom_url = alert['generatorURL']
        result['message'] = '{}\n\nsource: {}'.format(
            alert['annotations']['description'], prom_url)

        if alert['labels'].get('kba'):
            result['kba'] = {'number': alert['labels']['kba']}

        if alert['status'] == 'firing':
            result['urgency'] = focus_2_urgency[int(alert['labels']['focus'])]
        else:
            result['urgency'] = 'OK'

        results.append(result)
    return results

class TransHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        alerts = translate(data)
        headers = {'Authorization': 'Bearer {0}'.format(token)}
        for alert in alerts:
            json_alert = json.dumps(alert)
            time.sleep(random.uniform(1,10000)/1000)
            api_response = requests.post(endpoint, headers=headers, data=json_alert)
            loginfo('{}:{} urgency {} return_code {}'.format(alert['ci']['name'], alert[
                        'component']['name'], alert['urgency'], api_response.status_code))
        self.send_response(api_response.status_code)
        self.end_headers()

if __name__ == '__main__':
    loginfo('config endpoint="{0}"'.format(endpoint))
    loginfo('config token="{0}"'.format("*" * len(token)))
    loginfo('config org="{0}"'.format(ci_organization))

    try:
        httpd = HTTPServer((bindto, 3080), TransHandler)
    except Exception as err:
        logerror('exception initializing: {0}'.format(err))
        sys.exit(1)
    loginfo('initialized and running')
        
    try:
        httpd.serve_forever()
    except Exception as err:
        logerror('exception encountered: {0}'.format(err))
        sys.exit(1)
