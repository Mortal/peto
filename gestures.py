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


def apply1(a, xy):
    axx, axy, ayx, ayy, atx, aty = a
    x, y = xy
    return (axx * x + ayx * y + atx, axy * x + ayy * y + aty)


def dot1(a, b):
    # [axx ayx atx] [x] = [x axx + y ayx + atx]
    # [axy ayy aty] [y]   [x axy + y ayy + aty]
    # lambda x, y: (axx * x + ayx * y + atx, axy * x + ayy * y + aty)
    axx, axy, ayx, ayy, atx, aty = a
    bxx, bxy, byx, byy, btx, bty = b
    # x, y = (
    #     axx * (bxx * x + byx * y + btx) + ayx * (bxy * x + byy * y + bty) + atx,
    #     axy * (bxx * x + byx * y + btx) + ayy * (bxy * x + byy * y + bty) + aty,
    # )
    # lambda x, y: (bxx * x + byx * y + btx, bxy * x + byy * y + bty)
    # lambda x, y: (
    #     # axx * (bxx * x + byx * y + btx) + ayx * (bxy * x + byy * y + bty) + atx,
    #     #
    #     # axx * bxx * x + axx * byx * y + axx * btx
    #     # + ayx * bxy * x + ayx * byy * y + ayx * bty
    #     # + atx,
    #     #
    #     (axx * bxx + ayx * bxy) * x
    #     + (axx * byx + ayx * byy) * y
    #     + axx * btx + ayx * bty + atx,
    #     #
    #     # axy * (bxx * x + byx * y + btx) + ayy * (bxy * x + byy * y + bty) + aty,
    #     #
    #     # axy * bxx * x + axy * byx * y + axy * btx
    #     # + ayy * bxy * x + ayy * byy * y + ayy * bty
    #     # + aty,
    #     #
    #     (axy * bxx + ayy * bxy) * x
    #     + (axy * byx + ayy * byy) * y
    #     + (axy * btx + ayy * bty + aty),
    # )
    return (
        axx * bxx + ayx * bxy,
        axy * bxx + ayy * bxy,
        axx * byx + ayx * byy,
        axy * byx + ayy * byy,
        axx * btx + ayx * bty + atx,
        axy * btx + ayy * bty + aty,
    )


def dot(a_s, b_s):
    return [dot1(a, b) for a in a_s for b in b_s]


def translation(x, y):
    return (1, 0, 0, 1, x, y)


# Identity transformation
ident = translation(0, 0)
assert dot1(ident, ident) == ident
assert apply1(ident, (4, 3)) == (4, 3)
# Translations
trsmallx = translation(16, 0)
trlargex = translation(32, 0)
assert dot1(trsmallx, trsmallx) == trlargex
trsmally = translation(0, 16)
trlargey = translation(0, 32)
assert dot1(trsmallx, (0, 0, 0, 0, 100, 1000)) == (0, 0, 0, 0, 116, 1000)
assert apply1(trsmallx, (4, 3)) == (20, 3)
translarge = dot([ident, trlargex], [ident, trlargey])
transsmall = dot(
    translarge,
    dot([ident, trsmallx], [ident, trsmally]),
)
# Rotations
rotccw = (0, -1, 1, 0, 0, 0)
inv = dot1(rotccw, rotccw)
assert dot1(inv, inv) == ident
rotcw = dot1(inv, rotccw)
assert rotcw != rotccw
assert dot1(rotccw, inv) == rotcw
assert dot1(rotcw, rotccw) == ident, (rotcw, rotccw, dot1(rotcw, rotccw))
assert dot1(rotccw, rotcw) == ident
assert dot1(inv, translation(4, 3)) == dot1(translation(-4, -3), inv)
assert dot1(rotccw, translation(1, 0)) == dot1(translation(0, -1), rotccw)
rot90tiny = dot1(trsmally, rotccw)
rot90small = dot1(trlargey, rotccw)
rot90large = dot1(dot1(trlargey, trlargey), rotccw)
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
rot4trans4 = dot(translarge, rot4small)
rot4trans16 = dot(transsmall, rot4tiny)
trans34 = dot(
    [ident, trsmallx, trlargex],
    dot([ident, trsmally], [ident, trlargey]),
)

symmetries = {
    'rgb(0%,0%,100%)': dot([ident, rot90large], trans34),
    'rgb(0%,0%,50.2%)': rot4trans16,
    'rgb(100%,0%,0%)': rot4trans4,
    'rgb(100%,64.7%,0%)': transsmall,
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
            print([apply1(symm, p) for p in gestures[k]])
            print('<br><svg width="64" height="64"><path style="fill:black;stroke:none" d="%s" transform="matrix(%s)" /></svg><hr />' % (glyphs[k], ",".join(map(str, symm))))


if __name__ == "__main__":
    main()
