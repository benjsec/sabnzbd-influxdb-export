#!/usr/bin/python

import argparse  # for arg parsing...
import logging
import os
import time
from datetime import datetime  # for obtaining and formattying time
from multiprocessing import Process

from influxdb import InfluxDBClient  # via apt-get install python-influxdb
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) # suppress unverified cert warnings

url_format = '{0}://{1}:{2}/sabnzbd/api?apikey={3}&output=json'

logging.getLogger()


def main():
    args = parse_args()
    url = get_url(args.sabnzbdwebprotocol, args.sabnzbdhost, args.sabnzbdport, args.sabnzbdapikey)
    influxdb_client = InfluxDBClient(args.influxdbhost, args.influxdbport, args.influxdbuser, args.influxdbpassword, args.influxdbdatabase)
    create_database(influxdb_client, args.influxdbdatabase)
    init_exporting(args.interval, url, influxdb_client)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export SABnzbd data to influxdb')
    parser.add_argument(
        '--interval', type=int, required=False,
        default=os.environ.get('INTERVAL', 5),
        help='Interval of export in seconds')
    parser.add_argument(
        '--sabnzbdwebprotocol', type=str, required=False,
        default=os.environ.get('SABNZBD_PROTOCOL', 'http'),
        help='SABnzbd web protocol (http)')
    parser.add_argument(
        '--sabnzbdhost', type=str, required=False,
        default=os.environ.get('SABNZBD_HOST', 'localhost'),
        help='SABnzbd host (e.g. test.com))')
    parser.add_argument(
        '--sabnzbdport', type=int, required=False,
        default=os.environ.get('SABNZBD_PORT', 8080),
        help='SABnzbd port')
    parser.add_argument(
        '--sabnzbdapikey', type=str, required=True,
        default=os.environ.get('SABNZBD_API_KEY', ''),
        help='SABnzbd API key')
    parser.add_argument(
        '--influxdbhost', type=str, required=False,
        default=os.environ.get('INFLUXDB_HOST', 'localhost'),
        help='InfluxDB host')
    parser.add_argument(
        '--influxdbport', type=int, required=False,
        default=os.environ.get('INFLUXDB_PORT', 8086),
        help='InfluxDB port')
    parser.add_argument(
        '--influxdbuser', type=str, required=False,
        default=os.environ.get('INFLUXDB_USER', ''),
        help='InfluxDB user')
    parser.add_argument(
        '--influxdbpassword', type=str, required=False,
        default=os.environ.get('INFLUXDB_PASSWORD', ''),
        help='InfluxDB password')
    parser.add_argument(
        '--influxdbdatabase', type=str, required=False,
        default=os.environ.get('INFLUXDB_DATABASE', 'sabnzbd'),
        help='InfluxDB database')
    return parser.parse_args()


def qstatus(url,influxdb_client):
    try:
        data = requests.get('{0}{1}'.format(url, '&mode=queue'), verify=False).json()

        if data:
            queue = data['queue']
            speed = float(queue['kbpersec'])
            total_mb_left = float(queue['mbleft']) # mbleft?
            total_jobs = float(queue['noofslots'])
            status = queue['status']
            
            json_body = [
            {
                "measurement": "qstatus",
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields" : {
                    "speed": speed,
                    "total_mb_left": total_mb_left,
                    "total_jobs": total_jobs,
                    "status": status
                }
            }]
            influxdb_client.write_points(json_body)
                
    except Exception as e:
        print str(e)
        pass

def server_stats(url,influxdb_client):
    try:
        data = requests.get('{0}{1}'.format(url, '&mode=server_stats'), verify=False).json()

        if data:
            total = long(data['total'])
            total_month = long(data['month'])
            total_week = long(data['week'])
            total_day = long(data['day'])

            json_body = [
            {
                "measurement": "server_stats",
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields" : {
                    "total": total,
                    "total_month": total_month,
                    "total_week": total_week,
                    "total_day": total_day
                }
            }]
            influxdb_client.write_points(json_body)
            
    except Exception as e:
        print str(e)
        pass

def create_database(influxdb_client, database):
    try:
        influxdb_client.query('CREATE DATABASE {0}'.format(database))
    except Exception:
        pass

def init_exporting(interval, url, influxdb_client):
    while True:
        queuestatus = Process(target=qstatus, args=(url,influxdb_client,))
        queuestatus.start()

        serverstats = Process(target=server_stats, args=(url,influxdb_client,))
        serverstats.start()

        time.sleep(interval)

def get_url(protocol,host,port,apikey):
    return url_format.format(protocol,host,port,apikey)

if __name__ == '__main__':
    main()
