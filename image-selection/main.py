import cv2
import numpy as np
import json
import random

# -------------------- DATA --------------------
points = []
rows = []
rects = []
generated_points = []

rx, ry = -1, -1
rect_drawing = False

def generate_auto_rectangles(image, rows, points, width_scale=0.7):
    h, w = image.shape[:2]

    auto_rects = []

    if len(rows) < 2:
        return auto_rects

    rows = sorted(rows)
    row_dist = np.median(np.diff(rows))

    rect_w = int(row_dist * width_scale)
    rect_h = int(row_dist)

    for y in rows:

        row_points = [(x, py) for (x, py) in points if abs(py - y) < row_dist * 0.3]

        if not row_points:
            continue

        # cluster horizontally
        row_points.sort()

        clusters = []
        current = [row_points[0]]

        for p in row_points[1:]:
            if abs(p[0] - current[-1][0]) < rect_w:
                current.append(p)
            else:
                clusters.append(current)
                current = [p]

        clusters.append(current)

        for c in clusters:
            xs = [p[0] for p in c]
            cx = int(np.mean(xs))

            x1 = cx - rect_w // 2
            x2 = cx + rect_w // 2

            y1 = int(y - rect_h // 2)
            y2 = int(y + rect_h // 2)

            auto_rects.append({
                "x1": max(0, x1),
                "y1": max(0, y1),
                "x2": min(w, x2),
                "y2": min(h, y2)
            })

    return auto_rects

def generate_row_rubble_points(image, rows, radius=10, threshold_factor=0.7, points_per_region=3):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    result = []

    for y in rows:
        y = int(y)
        if y < 0 or y >= h:
            continue

        row = gray[y, :].astype(np.float32)

        # smooth signal
        kernel = np.ones(radius * 2 + 1) / (radius * 2 + 1)
        smooth = np.convolve(255 - row, kernel, mode='same')

        max_val = np.max(smooth)
        threshold = max_val * threshold_factor

        # detect regions
        regions = []
        start = None

        for x in range(w):
            if smooth[x] > threshold:
                if start is None:
                    start = x
            else:
                if start is not None:
                    regions.append((start, x))
                    start = None

        if start is not None:
            regions.append((start, w - 1))

        # create points per region
        for (x1, x2) in regions:
            cx = (x1 + x2) // 2
            length = x2 - x1

            for i in range(points_per_region):
                offset = random.randint(-length // 4, length // 4)
                result.append((cx + offset, y))

    return result

def generate_rectangles_from_rows(image, rows, points, width_scale=0.7):
    h, w = image.shape[:2]

    rects = generate_rectangles_from_rows(warped, rows, generated_points)

    rows = sorted(rows)

    if len(rows) < 2:
        return rects

    row_dist = np.median(np.diff(rows))

    rect_w = int(row_dist * width_scale)
    rect_h = int(row_dist)

    for y in rows:

        # points near row
        row_points = [(x, py) for (x, py) in points if abs(py - y) < row_dist * 0.3]

        if not row_points:
            continue

        # cluster points into groups (IMPORTANT FIX)
        row_points.sort()

        cluster = []
        clusters = []

        for p in row_points:
            if not cluster:
                cluster.append(p)
                continue

            if abs(p[0] - cluster[-1][0]) < rect_w:
                cluster.append(p)
            else:
                clusters.append(cluster)
                cluster = [p]

        if cluster:
            clusters.append(cluster)

        # build rectangles from clusters
        for c in clusters:
            xs = [p[0] for p in c]
            cx = int(np.mean(xs))

            x1 = cx - rect_w // 2
            x2 = cx + rect_w // 2

            y1 = int(y - rect_h // 2)
            y2 = int(y + rect_h // 2)

            rects.append({
                "x1": max(0, x1),
                "y1": max(0, y1),
                "x2": min(w, x2),
                "y2": min(h, y2)
            })

    return rects

def generate_row_points_weighted(image, rows, n_per_row=15):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    points = []

    for y in rows:
        y = int(y)

        # avoid out-of-bounds
        if y < 0 or y >= h:
            continue

        row = gray[y, :]

        # invert so dark = high weight
        weights = 255 - row.astype(np.float32)

        # avoid division issues if row is flat
        weights += 1e-6

        # normalize to probability distribution
        probs = weights / weights.sum()

        # sample x positions based on probability
        xs = np.random.choice(w, size=n_per_row, replace=True, p=probs)

        for x in xs:
            points.append((int(x), y))

    return points

def show_light_dark_map(image, points=None):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)

    # draw points
    if points is not None:
        for (x, y) in points:
            cv2.circle(heatmap, (x, y), 4, (255, 255, 255), -1)

    # -------- COLOR LEGEND --------
    h = heatmap.shape[0]
    legend_w = 70
    legend = np.zeros((h, legend_w, 3), dtype=np.uint8)

    for i in range(h):
        value = int(255 * (1 - i / h))  # 255 top, 0 bottom
        color = cv2.applyColorMap(np.array([[value]], dtype=np.uint8), cv2.COLORMAP_JET)[0, 0]
        legend[i, :] = color

    # -------- NUMERIC LABELS --------
    steps = 5  # number of labels
    for i in range(steps + 1):
        y = int(i * (h / steps))
        val = int(255 * (1 - i / steps))

        cv2.putText(
            legend,
            str(val),
            (5, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

    # -------- COMBINE --------
    combined = np.hstack((heatmap, legend))

    cv2.imshow("Light/Dark Map", combined)


# -------------------- STEP 1: CORNERS --------------------
def click_corner(event, x, y, flags, param):
    global points

    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append((x, y))
        print("Corner:", x, y)

def order_points(pts):
    pts = np.array(pts, dtype="float32")
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def warp(img):
    rect = order_points(points)

    (tl, tr, br, bl) = rect

    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))

    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(img, M, (width, height))

# -------------------- STEP 2: ROWS --------------------
def row_event(event, x, y, flags, param):
    global rows, display_rows

    if event == cv2.EVENT_LBUTTONDOWN:
        rows.append(y)
        rows.sort()
        redraw_rows()

def redraw_rows():
    global display_rows

    display_rows = warped.copy()

    for i, y in enumerate(rows):
        cv2.line(display_rows, (0, y), (display_rows.shape[1], y), (255, 0, 0), 2)
        cv2.putText(display_rows, f"Row {i+1}", (10, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    cv2.imshow("Select Rows (ENTER)", display_rows)

#  -------------------- STEP 3: Data points --------------------
def generate_row_points(image, rows, n_per_row=15):
    h, w = image.shape[:2]
    points = []

    for y in rows:
        for _ in range(n_per_row):
            x = random.randint(0, w - 1)
            points.append((x, y))

    return points

# -------------------- STEP 4: RECTANGLES --------------------
def rect_event(event, x, y, flags, param):
    global rx, ry, rect_drawing, display_rects

    if event == cv2.EVENT_LBUTTONDOWN:
        rect_drawing = True
        rx, ry = x, y

    elif event == cv2.EVENT_MOUSEMOVE and rect_drawing:
        temp = display_rects.copy()
        cv2.rectangle(temp, (rx, ry), (x, y), (0, 255, 0), 2)
        cv2.imshow("Draw Rectangles", temp)

    elif event == cv2.EVENT_LBUTTONUP:
        rect_drawing = False

        x1, y1 = min(rx, x), min(ry, y)
        x2, y2 = max(rx, x), max(ry, y)

        rects.append({
            "x1": x1, "y1": y1,
            "x2": x2, "y2": y2
        })

        redraw_rects()

def remove_auto_rect(x, y):
    global auto_rects

    new_list = []

    for r in auto_rects:
        if not (r["x1"] <= x <= r["x2"] and r["y1"] <= y <= r["y2"]):
            new_list.append(r)

    auto_rects = new_list

def redraw_rects():
    global display_rects

    display_rects = warped.copy()

    # rows
    for y in rows:
        cv2.line(display_rects, (0, y), (display_rects.shape[1], y), (255, 0, 0), 2)

    # MANUAL rectangles (green)
    for r in rects:
        cv2.rectangle(display_rects,
                      (r["x1"], r["y1"]),
                      (r["x2"], r["y2"]),
                      (0, 255, 0), 2)

    # AUTO rectangles (red)
    for r in auto_rects:
        cv2.rectangle(display_rects,
                      (r["x1"], r["y1"]),
                      (r["x2"], r["y2"]),
                      (0, 0, 255), 2)

    # points
    for (x, y) in generated_points:
        cv2.circle(display_rects, (x, y), 2, (0, 0, 255), -1)

    cv2.imshow("Draw Rectangles", display_rects)

# -------------------- MAIN --------------------
img = cv2.imread("image-selection/box.jpg")

if img is None:
    print("Image not found")
    exit()

# -------- STEP 1: corners --------
cv2.imshow("Select 4 Corners", img)
cv2.setMouseCallback("Select 4 Corners", click_corner)

while len(points) < 4:
    cv2.waitKey(1)

cv2.destroyAllWindows()

warped = warp(img)

# -------- STEP 2: show heatmap immediately (NO points yet) --------
show_light_dark_map(warped)
cv2.waitKey(0)
cv2.destroyAllWindows()

# -------- STEP 3: row selection --------
display_rows = warped.copy()

cv2.imshow("Select Rows (ENTER)", display_rows)
cv2.setMouseCallback("Select Rows (ENTER)", row_event)

while True:
    cv2.imshow("Select Rows (ENTER)", display_rows)
    if cv2.waitKey(1) == 13:
        break

cv2.destroyAllWindows()

# -------- STEP 4: generate REAL weighted points --------
generated_points = generate_row_rubble_points(warped, rows)
auto_rects = generate_auto_rectangles(warped, rows, generated_points)
# OPTIONAL: show heatmap AGAIN with points on it
show_light_dark_map(warped, generated_points)
cv2.waitKey(0)
cv2.destroyAllWindows()

# -------- STEP 5: rectangle drawing --------
display_rects = warped.copy()



cv2.imshow("Draw Rectangles", display_rects)
cv2.setMouseCallback("Draw Rectangles", rect_event)

cv2.waitKey(0)
cv2.destroyAllWindows()

# -------------------- SAVE --------------------
data = {
    "rows": rows,
    "rectangles": rects
}

with open("image-selection/output.json", "w") as f:
    json.dump(data, f, indent=4)

print("Saved rows and rectangles to output.json")