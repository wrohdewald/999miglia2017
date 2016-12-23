#!/usr/bin/env python3
# -*- coding: utf-8 -*-

tmpdir='segdir'

import os, shutil, sys, zipfile, tempfile

import urllib3
import io

import gpxpy
import gpxpy.gpx


def getWaypoints(fileName):
    with open(fileName, 'r') as segFile:
        _ = gpxpy.parse(segFile)
        return _.waypoints


def getPoints(fileName):
    """returns the GPX segment from fileName, asserting that
    fileName contains only one segment"""

    with open(fileName, 'r') as segFile:
        _ = gpxpy.parse(segFile)
        assert len(_.tracks) == 1, '{} has {} tracks'.format(fileName, len(_.tracks))
        _ = _.tracks[0]
        assert len(_.segments) == 1, '{} has {} segments in track'.format(fileName, len(_.segments))
        _ = _.segments[0]
        return _.points

def trackFromSegments(partList):
    fullTrack = gpxpy.gpx.GPXTrack()
    fullTrack.segments.extend(partList)
    return fullTrack


class Part:

    http = urllib3.PoolManager()
    allParts = list()

    def __init__(self, segmentId):
        self.segmentId = segmentId
        request = self.http.request('GET', "http://export.openrunner.com/kml/exportImportGPX.php?rttype=0&id={}".format(segmentId))
        data = request.data.decode()
        f = io.StringIO(data)
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
            part.endWaypoint.name ='CP {}: {}'.format(idx+1, part.endWaypoint.name)
            part.endWaypoint.description ='Distance {}km uphill {}m\nClosing time (to be done)'.format(part.length, part.uphill)

    @staticmethod
    def parseParts(segmentIds):
        Part.allParts = list(Part(x) for x in segmentIds) 
        Part.setEndWaypoints()

Part.parseParts([6875583, 6875588, 6875600, 6875608, 6875873, 6875883, 6875889, 6875894, 6876542, 6875912, 6875939, 6876273, 6876301, 6876446, 6876412])



fullGpx = gpxpy.gpx.GPX()
fullGpx.waypoints = list(x.endWaypoint for x in Part.allParts)

segment = gpxpy.gpx.GPXTrackSegment()

allPoints = sum((x.points for x in Part.allParts), list())
for point in allPoints:
    point.remove_time()
segment.points =  allPoints

fullLength = sum(x.length for x in Part.allParts)
fullUphill = sum(x.uphill for x in Part.allParts)

print('the full track has {} points, {}km and {}m'.format(len(segment.points), fullLength, fullUphill))


track = gpxpy.gpx.GPXTrack()
track.segments.append(segment)

fullGpx.tracks.append(track)

with open('999.gpx', 'w') as fullFile:
    fullFile.write(fullGpx.to_xml())
