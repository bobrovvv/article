#!/usr/bin/env python3

from gps3 import gps3
from math import modf
import sys
import csv
import curses
from time import sleep
from datetime import datetime

filename = 'data.csv'
form = 'DMS'
units = 'metric'
host = 'qwe1'
port = 'qwe2'

CONVERSION = {'raw': (1, 1, 'm/s', 'meters'),
              'metric': (3.6, 1, 'kph', 'meters'),
              'nautical': (1.9438445, 1, 'kts', 'meters'),
              'imperial': (2.2369363, 3.2808399, 'mph', 'feet')}

def make_time(gps_datetime_str):
    """Makes datetime object from string object"""
    if not 'n/a' == gps_datetime_str:
        datetime_string = gps_datetime_str
        datetime_object = datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S")
        return datetime_object


def elapsed_time_from(start_time):
    """calculate time delta from latched time and current time"""
    time_then = make_time(start_time)
    time_now = datetime.utcnow().replace(microsecond=0)
    if time_then is None:
        return
    delta_t = time_now - time_then
    return delta_t


def satellites_used(feed):
    """Counts number of satellites used in calculation from total visible satellites
    Arguments:
        feed feed=data_stream.TPV['satellites']
    Returns:
        total_satellites(int):
        used_satellites (int):
    """
    total_satellites = 0
    used_satellites = 0

    if not isinstance(feed, list):
        return 0, 0

    for satellites in feed:
        total_satellites += 1
        if satellites['used'] is True:
            used_satellites += 1
    return total_satellites, used_satellites

def unit_conversion(thing, units, length=False):
    """converts base data between metric, imperial, or nautical units"""
    if 'n/a' == thing:
        return 'n/a'
    try:
        thing = round(thing * CONVERSION[units][0 + length], 2)
    except TypeError:
        thing = 'fubar'
    return thing, CONVERSION[units][2 + length]


def sexagesimal(sexathang, latlon, form ='DDD'):
    """
    Arguments:
        sexathang: (float), -15.560615 (negative = South), -146.241122 (negative = West)  # Apataki Carenage
        latlon: (str) 'lat' | 'lon'
        form: (str), 'DDD'|'DMM'|'DMS', decimal Degrees, decimal Minutes, decimal Seconds
    Returns:
        latitude: e.g., '15°33'38.214"S'
        longitude: e.g., '146°14'28.039"W'
    """
    cardinal = 'O'
    if not isinstance(sexathang, float):
        sexathang = 'n/a'
        return sexathang

    if latlon == 'lon':
        if sexathang > 0.0:
            cardinal = 'E'
        if sexathang < 0.0:
            cardinal = 'W'

    if latlon == 'lat':
        if sexathang > 0.0:
            cardinal = 'N'
        if sexathang < 0.0:
            cardinal = 'S'

    if 'RAW' in form:
        sexathang = '{0:4.9f}°'.format(sexathang)  # 4 to allow -100° through -179.999999° to -180°
        return sexathang

    if 'DDD' in form:
        sexathang = '{0:3.6f}°'.format(abs(sexathang))

    if 'DMM' in form:
        _latlon = abs(sexathang)
        minute_latlon, degree_latlon = modf(_latlon)
        minute_latlon *= 60
        sexathang = '{0}°{1:2.5f}\''.format(int(degree_latlon), minute_latlon)

    if 'DMS' in form:
        _latlon = abs(sexathang)
        minute_latlon, degree_latlon = modf(_latlon)
        second_latlon, minute_latlon = modf(minute_latlon * 60)
        second_latlon *= 60.0
        sexathang = '{0}°{1}\'{2:2.3f}\"'.format(int(degree_latlon), int(minute_latlon), second_latlon)

    return sexathang + cardinal

def writeheader():
    with open (filename, 'a', newline='') as csv_file:
           columns = ['Time','Latitude','Longitude','Altitude','Speed']
           writer = csv.writer(csv_file)
           writer.writerow(columns)

def shut_down():
    """Closes connection and restores terminal"""
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    gpsd_socket.close()
    print('Keyboard interrupt received\nTerminated by user\nGood Bye.\n')
    sys.exit(1)

def show_human():
    try:
        for new_data in gpsd_socket:
            if new_data:
                data_stream.unpack(new_data)
                time = make_time(data_stream.TPV['time'].split('.')[0])
                lat =  sexagesimal(data_stream.TPV['lat'], 'lat', form)
                lon =  sexagesimal(data_stream.TPV['lon'], 'lon', form)
                alt = unit_conversion(data_stream.TPV['alt'], units, length=True)
                speed = unit_conversion(data_stream.TPV['speed'], units)
                data_window = curses.newwin(14, 50, 0, 0)
                data_window.clear()
                data_window.box()
                data_window.addstr(2, 2, 'Time: {} '.format(time))
                data_window.addstr(4, 2, 'Latitude: {} '.format(lat))
                data_window.addstr(6, 2, 'Longitude: {} '.format(lon))
                data_window.addstr(8, 2, 'Altitude: {} '.format(alt))
                data_window.addstr(10, 2, 'Speed: {} '.format(speed))
                data_window.refresh()
                data_window2 = curses.newwin(26, 50, 0, 52)
                data_window2.clear()
                data_window2.box()
                data_window2.addstr(2, 2, 'Heading:   {track}° True'.format(**data_stream.TPV))
                data_window2.addstr(4, 2, 'Climb:     {} {}/s'.format(*unit_conversion(data_stream.TPV['climb'], units, length=True)))
                data_window2.addstr(6, 2, 'Status:     {mode:<}D  '.format(**data_stream.TPV))
                data_window2.addstr(8, 2, 'Latitude Err:  +/-{} {} '.format(*unit_conversion(data_stream.TPV['epx'], units, length=True)))
                data_window2.addstr(10, 2, 'Longitude Err: +/-{} {}'.format(*unit_conversion(data_stream.TPV['epy'], units, length=True)))
                data_window2.addstr(12, 2, 'Altitude Err:  +/-{} {} '.format(*unit_conversion(data_stream.TPV['epv'], units, length=True)))
                data_window2.addstr(14, 2, 'Course Err:    +/-{epc}  '.format(**data_stream.TPV), curses.A_DIM)
                data_window2.addstr(16, 2, 'Speed Err:     +/-{} {} '.format(*unit_conversion(data_stream.TPV['eps'], units)), curses.A_DIM)
                data_window2.addstr(18, 2, 'Time Offset:   +/-{ept}  '.format(**data_stream.TPV), curses.A_DIM)
                data_window2.addstr(20, 2, 'gdop:{gdop}  pdop:{pdop}  tdop:{tdop}'.format(**data_stream.SKY))
                data_window2.addstr(22, 2, 'ydop:{ydop}  xdop:{xdop} '.format(**data_stream.SKY))
                data_window2.addstr(24, 2, 'vdop:{vdop}  hdop:{hdop} '.format(**data_stream.SKY))
                data_window2.refresh()

                sat_window = curses.newwin(18, 50, 16, 0)
                sat_window.clear()
                sat_window.box()

                sat_window.addstr(2, 2, 'Using {0[1]}/{0[0]} satellites (truncated)'.format(satellites_used(data_stream.SKY['satellites'])))
                sat_window.addstr(4, 2, 'PRN     Elev   Azimuth   SNR   Used')
                line = 6
                if isinstance(data_stream.SKY['satellites'], list):  # Nested lists of dictionaries are strings before data is present
                    for sats in data_stream.SKY['satellites'][0:10]:
                        sat_window.addstr(line, 2, '{PRN:>2}   {el:>6}   {az:>5}   {ss:>5}   {used:}'.format(**sats))
                        line += 1
                sat_window.refresh()



                if not isinstance(data_stream.DEVICES['devices'], list):  # Local machines need a 'device' kick start
                    gpsd_socket.send('?DEVICES;')  # to have valid data I don't know why.
                device_window = curses.newwin(10, 50, 28, 52)
                device_window.clear()
                device_window.box()
                if isinstance(data_stream.DEVICES['devices'], list):  # Nested lists of dictionaries are strings before data is present.
                    for gizmo in data_stream.DEVICES['devices']:
                        start_time, _uicroseconds = gizmo['activated'].split('.')  # Remove '.000Z'
                        elapsed = elapsed_time_from(start_time)
                        device_window.addstr(1, 2, 'Activated: {}'.format(gizmo['activated']))
                        device_window.addstr(2, 2, 'Host: {0}:{1} {2}'.format(host, port, gizmo['path']))
                        device_window.addstr(3, 2, 'Driver:{driver}     BPS:{bps}'.format(**gizmo))
                        device_window.addstr(4, 2, 'Cycle:{0} Hz {1!s:>14} Elapsed'.format(1 / gizmo['cycle'], elapsed))
                device_window.refresh()

                data = {'Time':time,'Latitude':lat,'Longitude':lon,'Altitude':alt[0],'Speed':speed[0]}

                with open(filename, "a", newline="") as csv_file:
                    columns = ['Time','Latitude','Longitude','Altitude','Speed']
                    writer = csv.DictWriter(csv_file, fieldnames=columns)
                    writer.writerow(data)
            else:
                sleep(.1)
    except KeyboardInterrupt:
        shut_down()
    except (OSError, IOError) as error:
        gpsd_socket.close()
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        sys.stderr.write('\rHUMAN error--> {}'.format(error))
        sys.stderr.write('\rhuman connection to gpsd at \'{0}\' on port \'{1}\' failed.\n'.format(host, port))
        sys.exit(1)  # TODO: gpsd existence check and start

if __name__ == '__main__':
    gpsd_socket = gps3.GPSDSocket()
    gpsd_socket.connect()
    gpsd_socket.watch()
    data_stream = gps3.DataStream()
    screen = curses.initscr()
    screen.clear()
    screen.scrollok(True)
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    writeheader()
    show_human()
