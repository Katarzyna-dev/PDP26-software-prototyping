import time
import re
import math


class ScanningSystem:

    def __init__(self, cnc, sensor):
        self.cnc = cnc
        self.sensor = sensor


    # Scanning
    def scan_line(self, length=300, feed=200, threshold=50):

        detections = []

        self.cnc.send_command(f"G1 X{length} F{feed}")
        

        while True:

            status = self.cnc.get_position()
            if status is None:
                continue

            x, y, z = self._parse_position(status)

            distance = self.sensor.get_distance()

            if distance is not None and distance < threshold:
                detections.append((x, y))

            if "Idle" in status:
                break

            time.sleep(0.01)

        return detections


    # Clustering
    def cluster_detections(self, detections, cluster_radius=15):
        """
        Groups nearby detection points into clusters.
        Returns list of (x, y) cluster centers.
        """

        clusters = []

        for point in detections:
            x, y = point
            added = False

            for cluster in clusters:
                cx, cy, points = cluster

                dist = math.hypot(x - cx, y - cy)

                if dist < cluster_radius:
                    points.append((x, y))

                    # Update cluster center (mean)
                    avg_x = sum(p[0] for p in points) / len(points)
                    avg_y = sum(p[1] for p in points) / len(points)

                    cluster[0] = avg_x
                    cluster[1] = avg_y

                    added = True
                    break

            if not added:
                clusters.append([x, y, [(x, y)]])

        # Return only centers
        return [(c[0], c[1]) for c in clusters]


    # Movement
    def interact_with_objects(self, coordinates, dip_depth=10):

        for x, y in coordinates:

            self.cnc.move_absolute(x=x, y=y, feed=800)

            self.cnc.move_relative(dz=-dip_depth, feed=400)
            self.cnc.move_relative(dz=dip_depth, feed=400)


    # Utility
    def _parse_position(self, status_line):

        match = re.search(r"MPos:([^|]+)", status_line)
        if not match:
            return 0, 0, 0

        coords = match.group(1).split(",")
        return float(coords[0]), float(coords[1]), float(coords[2])