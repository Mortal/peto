import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple


def try_parse_gesture(path_data: str) -> Optional[List[Tuple[float, float]]]:
    toks = path_data.split()
    i = 0
    points = []
    while i < len(toks):
        if i + 2 >= len(toks):
            return None
        if not points:
            if toks[i] != "M":
                return None
        else:
            if toks[i] != "L":
                return None
        points.append((float(toks[i + 1]), float(toks[i + 2])))
        i += 3
    return points


def dot1(a, b):
    axx, axy, ayx, ayy, atx, aty = a
    bxx, bxy, byx, byy, btx, bty = b
    # x, y = (
    #     axx * (bxx * x + bxy * y + btx) + axy * (byx * x + byy * y + bty) + atx,
    #     ayx * (bxx * x + bxy * y + btx) + ayy * (byx * x + byy * y + bty) + aty,
    # )
    # lambda x, y: (axx * x + axy * y + atx, ayx * x + ayy * y + aty)
    # lambda x, y: (bxx * x + bxy * y + btx, byx * x + byy * y + bty)
    # lambda x, y: (
    #     # axx * (bxx * x + bxy * y + btx) + axy * (byx * x + byy * y + bty) + atx,
    #     #
    #     # axx * bxx * x + axx * bxy * y + axx * btx
    #     # + axy * byx * x + axy * byy * y + axy * bty
    #     # + atx,
    #     #
    #     (axx * bxx + axy * byx) * x
    #     + (axx * bxy + axy * byy) * y
    #     + axx * btx + axy * bty + atx,
    #     #
    #     # ayx * (bxx * x + bxy * y + btx) + ayy * (byx * x + byy * y + bty) + aty,
    #     #
    #     # ayx * bxx * x + ayx * bxy * y + ayx * btx
    #     # + ayy * byx * x + ayy * byy * y + ayy * bty
    #     # + aty,
    #     #
    #     (ayx * bxx + ayy * byx) * x
    #     + (ayx * bxy + ayy * byy) * y
    #     + (ayx * btx + ayy * bty + aty),
    # )
    return (
        axx * bxx + axy * byx,
        axx * bxy + axy * byy,
        ayx * bxx + ayy * byx,
        ayx * bxy + ayy * byy,
        axx * btx + axy * bty + atx,
        ayx * btx + ayy * bty + aty,
    )


def dot(a_s, b_s):
    return [dot1(a, b) for a in a_s for b in b_s]


# Identity transformation
ident = (1, 0, 0, 1, 0, 0)
# Translations
trsmallx = (1, 0, 0, 1, 16, 0)
trlargex = (1, 0, 0, 1, 32, 0)
trsmally = (1, 0, 0, 1, 0, 16)
trlargey = (1, 0, 0, 1, 0, 32)
translarge = dot([ident, trlargex], [ident, trlargey])
transsmall = dot(
    translarge,
    dot([ident, trsmallx], [ident, trsmally]),
)
# Rotations
rotccw = (0, -1, 1, 0, 0, 0)
rot90tiny = dot1(trsmally, rotccw)
rot90small = dot1(trlargey, rotccw)
rot90large = dot1(dot1(trlargex, trlargex), rotccw)
rot180tiny = dot1(rot90tiny, rot90tiny)
rot180small = dot1(rot90small, rot90small)
rot180large = dot1(rot90large, rot90large)
rot2tiny = [ident, rot90tiny]
rot4tiny = dot([ident, rot180tiny], rot2tiny)
rot2small = [ident, rot90small]
rot4small = dot([ident, rot180small], rot2small)
rot2large = [ident, rot90large]
rot4large = dot([ident, rot180large], rot2large)
# Combinations
rot4trans4 = dot(translarge, rot4large)
rot4trans16 = dot(transsmall, rot4small)
rot2trans16 = dot(transsmall, rot2small)

symmetries = {
    'rgb(0%,0%,100%)': rot2trans16,
    'rgb(0%,0%,50.2%)': [ident, rotccw, trsmally, rot90tiny, rot180tiny],
    'rgb(100%,0%,0%)': rot4trans4,
    'rgb(100%,64.7%,0%)': rot2trans16,
    'rgb(62.7%,12.5%,94.1%)': rot4trans4,
    'rgb(64.7%,16.5%,16.5%)': rot4trans4,
}


def main() -> None:
    root = ET.parse("gestures.svg").getroot()
    paths = root.findall(".//svg:path", {"svg": "http://www.w3.org/2000/svg"})
    glyphs = {}
    gestures = {}
    for path in paths:
        css = {k.strip(): v.strip() for kv in path.attrib["style"].split(";") if kv.count(":") == 1 for k, v in [kv.split(":")]}
        stroke = css["stroke"]
        path_data = path.attrib["d"]
        gesture = try_parse_gesture(path_data)
        if gesture is None:
            ex = glyphs.setdefault(stroke, path_data)
            if ex != path_data:
                print("warning: Duplicate glyph for %r" % (stroke,))
        else:
            ex = gestures.setdefault(stroke, gesture)
            if ex != gesture:
                print("warning: Duplicate gesture for %r" % (stroke,))
    print("<!DOCTYPE html>")
    for k in sorted(glyphs.keys() & gestures.keys()):
        print("<h1>%s</h1>" % k)
        for symm in symmetries[k]:
            print('<svg width="64" height="64"><path style="fill:black;stroke:none" d="%s" transform="matrix(%s)" /></svg><hr />' % (glyphs[k], ",".join(map(str, symm))))
            # print(repr(k), glyphs[k], gestures[k])


if __name__ == "__main__":
    main()
