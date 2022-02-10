"""
Converts a GPX Route to a Track for sharing with Garmin Explore on iOS

This is a Pythonista 3 script for converting a GPX Route exported from Gaia
GPS into a GPX Track suitable for import into Garmin Explore.

See https://github.com/mshroyer/pythonista-scripts for the latest version.

"""

__author__ = "Mark Shroyer <mark@shroyer.name>"
__copyright__ = "Copyright 2022 Mark Shroyer"
__license__ = "Apache License 2.0"


import appex
import dialogs
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


GPXNS = "http://www.topografix.com/GPX/1/1"


def convert_element_to_string(ele):
    return ET.tostring(ele, encoding="UTF-8").decode("utf-8")


def convert_route_to_track(gpx):
    """Converts a string GPX route to a GPX track

    But doesn't add timestamps to trkpt nodes, on the assumption that Garmin
    Explore doesn't require them.

    """

    ET.register_namespace("", GPXNS)
    route_root = ET.fromstring(gpx)

    # If the GPX data doesn't contain a route (for example, maybe it's already
    # a track, which can be the case with some courses that were created by
    # importing existing GPX files into Gaia GPS), just return it verbatim
    # without attempting any conversion.
    if not route_root.find("{{{0}}}rte".format(GPXNS)):
        return gpx

    track_root = ET.Element("gpx", route_root.attrib)
    track_root.append(route_root.find("{{{0}}}metadata".format(GPXNS)))

    for rte in route_root.iter("{{{0}}}rte".format(GPXNS)):
        trk = ET.SubElement(track_root, "trk", {})
        for name in route_root.iter("{{{0}}}name".format(GPXNS)):
            if name.text is not None:
                trk.append(name)
                break

        trkseg = ET.SubElement(trk, "trkseg", {})
        for pt in rte.iter("{{{0}}}rtept".format(GPXNS)):
            pt.tag = "{{{0}}}trkpt".format(GPXNS)
            trkseg.append(pt)

    # Also copy over explicit waypoints in the source file. These may be
    # present if we export from Gaia GPS a folder containing both a route and
    # one or more waypoints.
    for wpt in route_root.iter("{{{0}}}wpt".format(GPXNS)):
        track_root.append(wpt)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        + convert_element_to_string(track_root)
    )


def main():
    if not appex.is_running_extension():
        print("This script is intended to run from the sharing extension")
        return

    gpx_route_path = Path(appex.get_text())
    with open(gpx_route_path, "r") as f:
        gpx_route = f.read()

    gpx_track = convert_route_to_track(gpx_route)

    with tempfile.TemporaryDirectory() as td:
        gpx_path = Path(td) / gpx_route_path.name
        with open(gpx_path, "w") as f:
            f.write(gpx_track)
        uri = gpx_path.resolve().as_uri()
        dialogs.share_url(uri)

    appex.finish()


if __name__ == "__main__":
    main()
