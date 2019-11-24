#!/usr/bin/env python3
#
# API adapter from Prometheus Alertmanager to UW AlertAPI
#   ssh://git@git.s.uw.edu/ue/monitoring.git

# All options via environment variables
#  ALERTAPI_TOKEN - token for AlertAPI access
#  ALERTAPI_URL - URL for AlertAPI, not including path
#  ALERT_ORGANIZATION - Service Now Organization Name

from flask import Flask, Response, request, abort, jsonify
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Summary
import json
import requests
import socket
import time
import random
import os
import sys
import signal

# Some logging systems like stackdriver distinguish between stdout and stderr
def loginfo(msg):
    print('am2alertapi info: {0}'.format(msg), file=sys.stdout, flush=True )

def logerror(msg):
    print('am2alertapi error: {0}'.format(msg), file=sys.stderr, flush=True)

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

if not 'ALERTAPI_URL' in os.environ:
    logerror('environment ALERTAPI_URL not set')
    sys.exit(1)

if not 'ALERT_ORGANIZATION' in os.environ:
    logerror('environment ALERT_ORGANIZATION not set')
    sys.exit(1)

ci_organization = os.environ['ALERT_ORGANIZATION']
token = os.environ['ALERTAPI_TOKEN']
api_url = os.environ['ALERTAPI_URL'].rstrip('/')
alert_endpoint = api_url + '/v1/alert'
keepalive_endpoint = api_url + '/v1/keepalive'

loginfo('config url="{0}"'.format(api_url))
loginfo('config alert_endpoint="{0}"'.format(alert_endpoint))
loginfo('config keepalive_endpoint="{0}"'.format(keepalive_endpoint))
loginfo('config token="{0}"'.format("*" * len(token)))
loginfo('config org="{0}"'.format(ci_organization))

REQUEST_TIME = Summary('am2alertapi_request', 'Time handling request')
server = Flask(__name__)

def translate(amalert):
    results = []
    try:
        for alert in amalert['alerts']:
            result = {}
            result['ci'] = {}
            result['component'] = {}
            result['message'] = ''
            result['ci']['organization'] = ci_organization

            # Heirarchy of ci selection
            if alert['labels'].get('hostname'):
                result['ci']['name'] = alert['labels']['hostname']
            if alert['labels'].get('cluster'):
                result['ci']['name'] = alert['labels']['cluster']
            if alert['labels'].get('ci_name'):
                result['ci']['name'] = alert['labels']['ci_name']
            if alert['labels'].get('ci_sysid'):
                result['ci']['sysid'] = alert['labels']['ci_sysid']

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

            if alert['labels'].get('watchdog_timeout'):
                result['timeout'] = alert['labels']['watchdog_timeout']

            results.append(result)

    except LookupError as e:
        logerror("Alert input missing required labels/annotations/attributes: {}".format(e))
        abort(406, description="Missing required labels/annotations/attributes {}".format(e))

    return results


@server.route('/', methods=['POST'])
@REQUEST_TIME.time()
def alert():
    """Submit posted alertmanager alerts to UW alertAPI"""
    headers = {'Authorization': 'Bearer {0}'.format(token)}

    data = request.get_json(force=True, silent=False, cache=True)
    alerts = translate(data)    
    for alert in alerts:
        json_alert = json.dumps(alert)
        time.sleep(random.uniform(1,10000)/1000)
        try:
            api_response = requests.post(alert_endpoint, headers=headers, data=json_alert, timeout=10)
        except requests.exceptions.Timeout:
            logerror('timeout with alertAPI')
            abort(500, description="timeout with alertapi")
        except ConnectionError:
            logerror('unable to connect with alertAPI')
            abort(500, description="connect error with alertapi")
        else:
            loginfo('alert {}:{} urgency {} return_code {}'.format(alert['ci']['name'], 
                alert['component']['name'], alert['urgency'], api_response.status_code))

    return Response(status=api_response.status_code)


@server.route('/watchdog', methods=['POST'])
@REQUEST_TIME.time()
def watchdog():
    """A watchdog using UW alertAPI keepalive.

    Watchdog expects a firing alert at a regular interval
    and will call alertAPI when the firing alert is missing.
    Contact must be made before the value of the label
    watchdog_timeout, which defaults to 5 minutes.
    """
    headers = {'Authorization': 'Bearer {0}'.format(token)}
    
    data = request.get_json(force=True, silent=False, cache=True)
    alerts = translate(data)
    for alert in alerts:
        if not alert.get('timeout'):
            alert['timeout'] = 5
        json_alert = json.dumps(alert)
        try:
            api_response = requests.post(keepalive_endpoint, headers=headers, data=json_alert, timeout=10)
        except requests.exceptions.Timeout:
            logerror('timeout with alertAPI')
            abort(500, description="timeout with alertapi")
        except ConnectionError:
            logerror('connect error with alertAPI')
            abort(500, description="connect error with alertapi")
        else:
            loginfo('keepalive {}:{} urgency {} timeout {} return_code {}'.format(alert['ci']['name'], 
                alert['component']['name'], alert['urgency'], alert['timeout'], api_response.status_code))

    return Response(status=api_response.status_code)


@server.route('/healthz')
def healthz():
    """Return a 200 illustrating responsiveness."""
    return Response(status=200)

@server.route('/metrics')
@REQUEST_TIME.time()
def metrics():
    """Return Prometheus metrics.""" 
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
