"""
Converts a GPX Route to a Track for sharing with Garmin Explore on iOS

This is a Pythonista 3 script intended to be used 

"""

import appex
import dialogs
import os
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
    track_root = ET.Element("gpx", route_root.attrib)

    track_root.append(route_root.find("{{{0}}}metadata".format(GPXNS)))
    trk = ET.SubElement(track_root, "trk", {})
    for name in route_root.iter("{{{0}}}name".format(GPXNS)):
        if name.text is not None:
            trk.append(name)
            break

    trkseg = ET.SubElement(trk, "trkseg", {})
    for rte in route_root.iter("{{{0}}}rte".format(GPXNS)):
        for pt in rte.iter("{{{0}}}rtept".format(GPXNS)):
            pt.tag = "{{{0}}}trkpt".format(GPXNS)
            trkseg.append(pt)

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        + convert_element_to_string(track_root)
    )


def main():
    if not appex.is_running_extension():
        print("This script is intended to run from the sharing extension")
        return

    gpx_route_path = appex.get_text()
    with open(gpx_route_path, "r") as f:
        gpx_route = f.read()

    gpx_track = convert_route_to_track(gpx_route)

    with tempfile.TemporaryDirectory() as td:
        gpx_path = Path(td) / os.path.basename(gpx_route_path)
        with open(gpx_path, "w") as f:
            f.write(gpx_track)
        uri = gpx_path.resolve().as_uri()
        dialogs.share_url(uri)

    appex.finish()


if __name__ == "__main__":
    main()
