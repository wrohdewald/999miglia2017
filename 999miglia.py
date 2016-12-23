#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib3

import gpxpy
import gpxpy.gpx


class Part:

    http = urllib3.PoolManager()
    allParts = list()

    def __init__(self, segmentId):
        self.segmentId = segmentId
        request = self.http.request('GET', "http://export.openrunner.com/kml/exportImportGPX.php?rttype=0&id={}".format(segmentId))
        data = request.data.decode()
        self.gpx = gpxpy.parse(data)
        assert len(self.gpx.tracks) == 1, 'Openrunner ID {} has {} tracks'.format(segmentId, len(self.gpx.tracks))
        self.track = self.gpx.tracks[0]
#        self.track.simplify()
        assert len(self.track.segments) == 1, 'Openrunner ID {} has {} segments in track'.format(segmentId, len(self.track.segments))
        segment = self.track.segments[0]
        self.points = segment.points
        self.startName = self.track.name.split(':')[0].split('--')[1]
        self.length = round(self.track.length_2d()/1000.0)
        self.uphill = round(self.track.get_uphill_downhill()[0])
        firstPoint = self.points[0]
        # it is easier to extract the name of the starting place from the track name
        self.startWaypoint = gpxpy.gpx.GPXWaypoint(
            name=self.startName,
            latitude=firstPoint.latitude,
            longitude=firstPoint.longitude,
            elevation=firstPoint.elevation)
        self.endWaypoint = None

    @staticmethod
    def setEndWaypoints():
        waypointOrder = list(Part.allParts[1:] + Part.allParts[0:1])
        for src, dest in zip(waypointOrder, Part.allParts):
            dest.endWaypoint = src.startWaypoint
        for idx, part in enumerate(Part.allParts):
            part.endWaypoint.name = 'CP {}: {}'.format(idx+1, part.endWaypoint.name)
            part.endWaypoint.description = 'Distance {}km uphill {}m\nClosing time (to be done)'.format(part.length, part.uphill)

    @staticmethod
    def parseParts(segmentIds):
        Part.allParts = list(Part(x) for x in segmentIds)
        Part.setEndWaypoints()

    @staticmethod
    def createFullTrackFor(segmentIds, intoFileName):
        Part.parseParts(segmentIds)
        fullGpx = gpxpy.gpx.GPX()
        fullGpx.waypoints = list(x.endWaypoint for x in Part.allParts)
        segment = gpxpy.gpx.GPXTrackSegment()
        allPoints = sum((x.points for x in Part.allParts), list())
        for point in allPoints:
            point.remove_time()
        segment.points = allPoints

        fullLength = sum(x.length for x in Part.allParts)
        fullUphill = sum(x.uphill for x in Part.allParts)

        print('the full track has {} points, {}km and {}m'.format(len(segment.points), fullLength, fullUphill))


        track = gpxpy.gpx.GPXTrack()
        track.segments.append(segment)

        fullGpx.tracks.append(track)

        with open(intoFileName, 'w') as fullFile:
            fullFile.write(fullGpx.to_xml())

SEGMENTIDS = (6875583, 6875588, 6875600, 6875608, 6875873, 6875883, 6875889, 6875894, 6876542, 6875912, 6875939, 6876273, 6876301, 6876446, 6876412)

Part.createFullTrackFor(SEGMENTIDS, '999.gpx')
