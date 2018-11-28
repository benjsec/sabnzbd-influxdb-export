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
# suppress unverified cert warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

url_format = '{0}://{1}:{2}/sabnzbd/api?apikey={3}&output=json'

FORMAT = '%(asctime)s %(levelname)-8s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
log = logging.getLogger()


def main():
    args = parse_args()
    if args.verbose or os.environ.get('DEBUG'):
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)
    url = get_url(args.sabnzbdwebprotocol,
                  args.sabnzbdhost,
                  args.sabnzbdport,
                  args.sabnzbdapikey)
    log.debug("Using sabnzbd url: %s", url)
    influxdb_client = InfluxDBClient(args.influxdbhost,
                                     args.influxdbport,
                                     args.influxdbuser,
                                     args.influxdbpassword,
                                     args.influxdbdatabase)
    log.debug("Using influxdb: %s:%s",
              args.influxdbhost, args.influxdbport)
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
        '--sabnzbdapikey', type=str, required=False,
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
    loggroup = parser.add_mutually_exclusive_group()
    loggroup.add_argument(
        '-v', '--verbose', action='store_true',
        help='Enable verbose (debug) logging.')
    loggroup.add_argument(
        '-q', '--quiet', action='store_true',
        help='Only show log messages at warning level and higher.')
    return parser.parse_args()


def qstatus(url, influxdb_client):
    log.debug("Getting queue status")
    try:
        data = requests.get(
            '{0}{1}'.format(url, '&mode=queue'), verify=False).json()
    except Exception:
        log.exeption("Error getting queue status from sabnzbd.")

    if not data:
        log.debug("No data returned.")
        return
    log.debug("Data from sabnzbd: %s", data)

    queue = data['queue']
    try:
        speedlimit_abs = float(queue["speedlimit_abs"])
    except ValueError:
        speedlimit_abs = 0.0

    json_body = [{
        "measurement": "qstatus",
        "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "fields": {
            "speed": float(queue["kbpersec"]),
            "total_mb_left": float(queue["mbleft"]),
            "speedlimit": float(queue["speedlimit"]),
            "speedlimit_abs": speedlimit_abs,
            "total_jobs": float(queue["noofslots"]),
            "status": queue.get("status"),
            "timeleft": queue.get("timeleft"),
            "diskspace1": float(queue.get("diskspace1")),
            "diskspace2": float(queue.get("diskspace2")),
            "diskspacetotal1": float(queue.get("diskspacetotal1")),
            "diskspacetotal2": float(queue.get("diskspacetotal2")),
            "diskspace1_norm": queue.get("diskspace1_norm"),
            "diskspace2_norm": queue.get("diskspace2_norm"),
            "loadavg_1m": float(queue.get("loadavg").split('|')[0]),
            "loadavg_5m": float(queue.get("loadavg").split('|')[1]),
            "loadavg_15m": float(queue.get("loadavg").split('|')[2]),
            "have_warnings": queue.get("have_warnings"),
            "eta": queue.get("eta"),
        }
    }]
    try:
        influxdb_client.write_points(json_body)
    except Exception:
        log.exception("Error posting queue status to InfluxDB")


def server_stats(url, influxdb_client):
    log.debug("Getting server status.")
    try:
        data = requests.get(
            '{0}{1}'.format(url, '&mode=server_stats'), verify=False).json()
    except Exception:
        log.exception("Error getting server status from sabnzbd.")

    if not data:
        log.debug("No data received for server status.")
        return

    total = long(data['total'])
    total_month = long(data['month'])
    total_week = long(data['week'])
    total_day = long(data['day'])

    json_body = [
        {
            "measurement": "server_stats",
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "total": total,
                "total_month": total_month,
                "total_week": total_week,
                "total_day": total_day
            }
        }]

    try:
        influxdb_client.write_points(json_body)
    except Exception:
        log.exception("Error posting server status to InfluxDB.")


def create_database(influxdb_client, database):
    log.debug("Creating influxdb database %s", database)
    try:
        influxdb_client.query('CREATE DATABASE {0}'.format(database))
    except Exception:
        log.exeception("Error creating database in InfluxDB")


def init_exporting(interval, url, influxdb_client):
    log.info("Starting monitoring with interval of %ss", interval)
    while True:
        queuestatus = Process(target=qstatus, args=(url, influxdb_client,))
        queuestatus.start()

        serverstats = Process(
            target=server_stats, args=(url, influxdb_client,))
        serverstats.start()

        time.sleep(interval)


def get_url(protocol, host, port, apikey):
    return url_format.format(protocol, host, port, apikey)


if __name__ == '__main__':
    main()
