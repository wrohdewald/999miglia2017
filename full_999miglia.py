#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) Wolfgang Rohdewald <wolfgang@rohdewald.de>
# See LICENSE for details.

"""
This script creates one single track for the entire 999 Miglia 2017.
It adds waypoints for all checkpoints.
"""

import urllib3

import gpxpy
import gpxpy.gpx


class Part:

    """represents one segment of the full track"""

    # pylint: disable=too-many-instance-attributes

    http = urllib3.PoolManager()
    all_parts = list()

    def __init__(self, segment_id):
        self.segment_id = segment_id
        request = self.http.request(
            'GET',
            "http://export.openrunner.com/kml/exportImportGPX.php?rttype=0&id={}".format(
                segment_id))
        data = request.data.decode()
        self.gpx = gpxpy.parse(data)
        assert len(self.gpx.tracks) == 1, (
            'Openrunner ID {} has {} tracks'.format(segment_id, len(self.gpx.tracks)))
        self.track = self.gpx.tracks[0]
#        self.track.simplify()
        assert len(self.track.segments) == 1, \
            'Openrunner ID {} has {} segments in track'.format(segment_id, len(self.track.segments))
        segment = self.track.segments[0]
        self.points = segment.points
        self.start_name = self.track.name.split(':')[0].split('--')[1]
        self.length = round(self.track.length_2d()/1000.0)
        self.uphill = round(self.track.get_uphill_downhill()[0])
        first_point = self.points[0]
        # it is easier to extract the name of the starting place from the track name
        self.start_waypoint = gpxpy.gpx.GPXWaypoint(
            name=self.start_name,
            latitude=first_point.latitude,
            longitude=first_point.longitude,
            elevation=first_point.elevation)
        self.end_waypoint = None

    @staticmethod
    def set_end_waypoints():
        """adds endpoints to all segments"""
        waypoint_order = list(Part.all_parts[1:] + Part.all_parts[0:1])
        for src, dest in zip(waypoint_order, Part.all_parts):
            dest.end_waypoint = src.start_waypoint
        for idx, part in enumerate(Part.all_parts):
            part.end_waypoint.name = 'CP {}: {}'.format(idx+1, part.end_waypoint.name)
            part.end_waypoint.description = \
                'Distance {}km uphill {}m\nClosing time (to be done)'.format(
                    part.length, part.uphill)

    @staticmethod
    def parse_parts(segment_ids):
        """parses all segments and adds endpoints"""
        Part.all_parts = list(Part(x) for x in segment_ids)
        Part.set_end_waypoints()

    @staticmethod
    def create_full_track_for(segment_ids, into_filename):
        """combines all segments to one big track and writes into into_filename"""
        Part.parse_parts(segment_ids)
        full_gpx = gpxpy.gpx.GPX()
        full_gpx.waypoints = list(x.end_waypoint for x in Part.all_parts)
        segment = gpxpy.gpx.GPXTrackSegment()
        all_points = sum((x.points for x in Part.all_parts), list())
        for point in all_points:
            point.remove_time()
        segment.points = all_points

        full_length = sum(x.length for x in Part.all_parts)
        full_uphill = sum(x.uphill for x in Part.all_parts)

        print('the full track has {} points, {}km and {}m'.format(
            len(segment.points), full_length, full_uphill))


        track = gpxpy.gpx.GPXTrack()
        track.segments.append(segment)

        full_gpx.tracks.append(track)

        with open(into_filename, 'w') as full_file:
            full_file.write(full_gpx.to_xml())

SEGMENTIDS = (6875583, 6875588, 6875600, 6875608, 6875873, 6875883, 6875889, 6875894,
              6876542, 6875912, 6875939, 6876273, 6876301, 6876446, 6876412)

Part.create_full_track_for(SEGMENTIDS, '999.gpx')
