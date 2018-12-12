# sabnzbd-influxdb-export

This script will query SABnzbd to pull basic stats and store them in influxdb. Stay tuned for further additions!

Available as a docker image on dockerhub (https://hub.docker.com/r/benjsec/sabnzbd-influxdb-export)

## Parameters
  
Parameters can either be set at the commandline or by environment variable.
If both are use the commandline parameters take presedence.

| CommandLine | Environment | Notes | Default |
|---|---|---|---|
| --interval  | INTERVAL | In seconds | 5 |
| --sabnzbdwebprotocol  | SABNZBD_PROTOCOL | http/https | http |
| --sabnzbdhost  | SABNZBD_HOST |   | localhost |
| --sabnzbdport  | SABNZBD_PORT |   | 8080 |
| --sabnzbdapikey  | SABNZBD_API_KEY |   | empty |
| --influxdbhost  | INFLUXDB_HOST |   | localhost |
| --influxdbport  | INFLUXDB_PORT |   | 8086 |
| --influxdbuser  | INFLUXDB_USER |   | empty |
| --influxdbpassword  | INFLUXDB_PASSWORD |   | empty |
| --influxdbdatabase  | INFLUXDB_DATABASE |   | sabnzbd |


## Example

  ```Dockerfile
  sabnzbd_influx:
    image: benjsec/sabnzbd-influxdb-export
    hostname: sabnzb-influx
    environment:
      SABNZBD_HOST: sabnzbd_1
      SABNZBD_PORT: 8080
      SABNZBD_API_KEY: ...
      INFLUXDB_HOST: influxdb_1
      INFLUXDB_PORT: 8086
    restart: unless-stopped
  ```

## Exported Data
  * Queue
    - Status: A string indicating the current status, e.g. "Downloading"
    - total_jobs: *#* Jobs
    - total_mb_left: Total queue size (MB)
    - speed: Download Speed (kB/s)
    - speedlimit: Relative Speedlimit (percent)
    - speedlimit_abs: Absolute Speedlimit (bytes/s)
    - timeleft: The time remaining string as shown in SabNZBd
    - seconds_left: The number of seconds remaining
    - eta: The expected finish date string as shown in SabNZBd
    - eta_timestamp: The unix timestamp of the expected finish date (ms)
    - have_warnings: The number of warnings currently registered in SabNZBd
    - loadavg_1m: The 1 minute load average on the server
    - loadavg_5m: The 5 minute load average on the server
    - loadavg_15m: The 15 minute load average on the server
    - diskspace1: The free disk space in the downloads path (GB)
    - diskspace2: The free disk space in the storage path (GB)
    - diskspacetotal1: The total disk space in the downloads path (GB)
    - diskspacetotal2: The total disk space in the storage path (GB)
    - diskspace1_norm: The disk space in the downloads path as string with units
    - diskspace2_norm: The disk space in the storage path as string with units
  * Server Stats
    - Total downloaded
    - Total downloaded (month)
    - Total downloaded (week)
    - Total downloaded (day)

### To Do:
  * Coming soon...

## Use-Case
  With the data exported to influxdb, you can create some useful stats/graphs in graphing tools such as grafana (http://grafana.org/)
  
  ![alt tag](https://user-images.githubusercontent.com/4528753/29847166-e912f8ec-8cdf-11e7-8dc0-7155435130f6.png)
  
  
