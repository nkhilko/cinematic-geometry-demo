"""Sample a two-phase pinhole-camera move around a synthetic planar artwork."""
import argparse
import json
import math
from pathlib import Path

WIDTH, HEIGHT = 360, 640
FOCAL = 420
HALF_ART = 0.6
FINAL_WIDTH = 0.84
FINAL_DEPTH = 2 * HALF_ART * FOCAL / (WIDTH * FINAL_WIDTH)
CORNERS = [(-HALF_ART, 0.8, 0), (HALF_ART, 0.8, 0), (HALF_ART, -0.8, 0), (-HALF_ART, -0.8, 0)]


def ease(t):
    return t * t * (3 - 2 * t)


def camera(t):
    if not 0 <= t <= 1:
        raise ValueError("Time must be normalized to the shot")
    if t < 0.6:
        angle = math.radians(34) * (1 - ease(t / 0.6))
        return (4.6 * math.sin(angle), 0, 4.6 * math.cos(angle))
    return (0, 0, 4.6 + (FINAL_DEPTH - 4.6) * ease((t - 0.6) / 0.4))


def project(point, eye):
    x, y, z = (point[i] - eye[i] for i in range(3))
    length = math.hypot(eye[0], eye[2])
    right = (eye[2] / length, -eye[0] / length)
    depth = (eye[0] * -x + eye[2] * -z) / length
    if depth <= 0:
        raise ValueError("Point is behind the camera")
    return (WIDTH / 2 + FOCAL * (right[0] * x + right[1] * z) / depth,
            HEIGHT / 2 - FOCAL * y / depth)


def projected(eye, points):
    return " ".join(f"{x:.3f},{y:.3f}" for x, y in (project(p, eye) for p in points))


def contact_sheet(poses):
    samples = [(0, "Opening"), (30, "Frontal alignment"), (50, "Final framing")]
    polygons = [
        ("#fff", CORNERS),
        ("#242424", [(-0.42, -0.50, 0), (-0.22, 0.58, 0.0), (0.45, -0.38, 0)]),
        ("#777", [(-0.39, -0.62, 0), (0.43, -0.48, 0), (0.38, -0.63, 0)]),
    ]
    frames = []
    for column, (index, name) in enumerate(samples):
        eye = poses[index]
        shapes = "".join(f'<polygon fill="{fill}" points="{projected(eye, points)}"/>' for fill, points in polygons)
        frames.append(f'<g transform="translate({12 + column * 190} 20)">'
                      f'<svg width="175" height="311" viewBox="0 0 {WIDTH} {HEIGHT}">'
                      f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#e4e4e4"/>{shapes}</svg>'
                      f'<text x="0" y="335" font-size="13">{name}</text></g>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 582 370" role="img">'
            '<title>Three views of a synthetic artwork during a two-phase camera move</title>'
            '<rect width="582" height="370" fill="white"/>'
            '<g font-family="sans-serif">' + "".join(frames) + '</g></svg>\n')


def inspect(poses):
    center_error = max(math.dist(project((0, 0, 0), eye), (WIDTH / 2, HEIGHT / 2)) for eye in poses)
    axial_error = max(abs(eye[0]) for eye in poses[30:])
    end = [project(corner, poses[-1]) for corner in CORNERS]
    ratio = (end[1][0] - end[0][0]) / WIDTH
    scale = math.dist(end[0], end[1]) / math.dist(end[1], end[2])
    if not (center_error < 1e-9 and axial_error == 0 and abs(ratio - FINAL_WIDTH) < 1e-9
            and abs(scale - 0.75) < 1e-9
            and all(0 <= x <= WIDTH and 0 <= y <= HEIGHT for x, y in end)):
        raise RuntimeError("Shot failed projection checks")
    return {"samples": len(poses), "max_target_error_px": center_error,
            "axial_error": axial_error, "final_width_fraction": ratio, "final_artwork_aspect": scale}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("out"))
    args = parser.parse_args()
    poses = [camera(frame / 50) for frame in range(51)]
    checks = inspect(poses)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "camera-path.json").write_text(json.dumps({"checks": checks, "positions": poses}, indent=2) + "\n")
    (args.output / "contact-sheet.svg").write_text(contact_sheet(poses))
    print(json.dumps(checks, indent=2))
