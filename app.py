import html
import math
import typing
from collections import namedtuple
from functools import partial

from flask import Flask

E10 = math.sqrt(50)
E5 = math.sqrt(10)
E2 = math.sqrt(2)


def getter_x(d):
    return d["x"]


def getter_y(d):
    return d["y"]


def get_ticks(start, stop, count=5):
    i = 0

    if start == stop and count > 0:
        return [start]

    reverse = stop < start
    if reverse:
        start, stop = stop, start
    step = increment(start, stop, count)
    if step == 0 or not math.isfinite(step):
        return []

    if step > 0:
        start = math.ceil(start / step)
        stop = math.floor(stop / step)
        n = math.ceil(stop - start + 1)
        ticks = []
        while i < n:
            ticks.append((start + i) * step)
            i += 1
    else:
        start = math.floor(start * step)
        stop = math.ceil(stop * step)
        n = math.ceil(start - stop + 1)
        ticks = []
        while i < n:
            ticks.append((start - i) / step)
            i += 1

    if reverse:
        ticks.reverse()

    return [int(t) if t.is_integer() else t for t in ticks]


def increment(start, stop, count):
    step = (stop - start) / max(0, count)
    power = math.floor(math.log(step) / math.log(10))
    error = step / math.pow(10, power)

    if power >= 0:
        return (
            10 if error >= E10 else 5 if error >= E5 else 2 if error >= E2 else 1
        ) * math.pow(10, power)
    else:
        -math.pow(10, -power) / (
            10 if error >= E10 else 5 if error >= E5 else 2 if error >= E2 else 1
        )


style = """
.chart {
    height: 100%;
    padding: 3em 2em 2em 3em;
    box-sizing: border-box;
}

.axes {
    width: 100%;
    height: 100%;
    border-left: 1px solid black;
    border-bottom: 1px solid black;
}

.y.label {
    position: absolute;
    left: -2.5em;
    width: 2em;
    text-align: right;
    bottom: -0.5em;
}

.x.label {
    position: absolute;
    width: 4em;
    left: -2em;
    bottom: -22px;
    font-family: sans-serif;
    text-align: center;
}

path.data {
    stroke: red;
    stroke-linejoin: round;
    stroke-linecap: round;
    stroke-width: 2px;
    fill: none;
}

pancake-chart {
    position: relative;
    display: block;
    width: 100%;
    height: 100%;
}

pancake-box {
    position: absolute;
}

pancake-grid-item {
    position: absolute;
    left: 0;
    top: 0;
}

svg {
    position: absolute;
    width: 100%;
    height: 100%;
    overflow: visible;
}

svg * {
    vector-effect: non-scaling-stroke;
}

// second

.grid-line {
    position: relative;
    display: block;
}

.grid-line.horizontal {
    width: calc(100% + 2em);
    left: -2em;
    border-bottom: 1px dashed #ccc;
}

.grid-line.vertical {
    height: 100%;
    border-left: 1px dashed #ccc;
}

.grid-line span {
    position: absolute;
    left: 0;
    bottom: 2px;
    line-height: 1;
    font-family: sans-serif;
    font-size: 14px;
    color: #999;
}

.year-label {
    position: absolute;
    width: 4em;
    left: -2em;
    bottom: -30px;
    font-family: sans-serif;
    font-size: 14px;
    color: #999;
    text-align: center;
}

.text {
    position: absolute;
    width: 15em;
    line-height: 1;
    color: #666;
    transform: translate(0,-50%);
    text-shadow: 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white, 0 0 8px white;
}

.text p {
    margin: 0;
    line-height: 1.2;
    color: #999;
}

.text h2 {
    margin: 0;
    font-size: 1.4em;
}

path.avg {
    stroke: #676778;
    opacity: 0.5;
    stroke-linejoin: round;
    stroke-linecap: round;
    stroke-width: 1px;
    fill: none;
}

path.scatter {
    stroke-width: 3px;
}

path.trend {
    stroke: #ff3e00;
    stroke-linejoin: round;
    stroke-linecap: round;
    stroke-width: 2px;
    fill: none;
}
pancake-point {
    position: absolute;
    width: 0;
    height: 0;
}
"""


def linear(domain, range):
    d0 = domain[0]
    r0 = range[0]
    m = (range[1] - r0) / (domain[1] - d0)

    def resolve(num):
        return r0 + (num - d0) * m

    return resolve


TAGS = [
    "html",
    "head",
    "style",
    "body",
    "h1",
    "h2",
    "div",
    "p",
    "em",
    "span",
    "svg",
    "path",
    "d",
]


class HyperScript:
    def __init__(self):
        for tag in TAGS:
            setattr(self, tag, partial(self, tag))

    def __call__(self, tag, attrs=None, children=None):
        attrs = {} if attrs is None else attrs
        children = [] if children is None else children
        a = " ".join(
            f'class="{html.escape(str(v))}"'
            if k == "className"
            else f'{html.escape(k)}="{html.escape(str(v))}"'
            for k, v in attrs.items()
        )
        return f"<{tag} {a}>{''.join(str(c) for c in children)}</{tag}>"


h = HyperScript()


class BaseHNode:
    children: typing.Optional[typing.List["HNode"]]

    def __str__(self) -> str:
        return "".join(str(c) for c in self.children) if self.children else ""


class HNode(BaseHNode):
    children: typing.Optional[typing.List["HNode"]]

    def __init__(
        self,
        children: typing.List[typing.Union[str, "HNode"]] = None,
        **props: typing.Any,
    ) -> None:
        self.props = props
        if children:
            self.children = [
                HString(children=c, dangerousHTML=props.get("dangerousHTML", False))
                if isinstance(c, str)
                else c
                for c in children
            ]
        else:
            self.children = children


class HTag(HNode):
    def __init__(
        self,
        tag,
        children: typing.List[typing.Union[str, "HNode"]] = None,
        **props: typing.Any,
    ) -> None:
        self.tag = tag
        super().__init__(children=children, **props)

    def __str__(self) -> str:
        return h(self.tag, self.props, self.children)


for tag in TAGS:
    setattr(HTag, tag, partial(HTag, tag))


class HString(BaseHNode):
    def __init__(
        self,
        children: typing.List[typing.Union[str, "HNode"]] = None,
        dangerousHTML=False,
        **props: typing.Any,
    ) -> None:
        self.props = props
        self.children = children if dangerousHTML else html.escape(children)

    def __str__(self) -> str:
        return self.children or ""


class Chart(HNode):
    def __str__(self) -> str:
        return h("pancake-chart", {}, self.children)


class Box(HNode):
    def __str__(self) -> str:
        return h(
            "pancake-box",
            {"style": "left: 0%; bottom: 0%; width: 100%; height: 100%;"},
            self.children,
        )


class GridItem(HNode):
    def __str__(self):
        return h(
            "pancake-grid-item",
            {"style": self.props["style"](self.props["value"])},
            self.props["renderer"](
                value=self.props["value"],
                first=self.props["first"],
                last=self.props["last"],
            ),
        )


class Grid(HNode):
    def __init__(
        self, count, context, renderer, ticks=None, horizontal=False, vertical=False
    ):
        super().__init__(renderer=renderer)
        scale_x, scale_y = context["scale_x"], context["scale_y"]
        self.ticks = ticks
        if horizontal:
            if ticks is None:
                self.ticks = get_ticks(context["min_y"], context["max_y"], count)
            self.style = lambda y: f"width: 100%; height: 0; top: {scale_y(y)}%"
        else:
            if ticks is None:
                self.ticks = get_ticks(context["min_x"], context["max_x"], count)
            self.style = lambda x: f"width: 0; height: 100%; left: {scale_x(x)}%"

    def __str__(self):
        lindex = len(self.ticks) - 1
        return h(
            "pancake-grid",
            {},
            [
                GridItem(
                    value=tick,
                    first=i == 0,
                    last=i == lindex,
                    style=self.style,
                    renderer=self.props["renderer"],
                )
                for i, tick in enumerate(self.ticks)
            ],
        )


class SvgLine(HNode):
    def __init__(self, points, context, renderer, x=getter_x, y=getter_y):
        super().__init__()
        scale_x, scale_y = context["scale_x"], context["scale_y"]
        d = "M" + "L".join((f"{scale_x(x(d))},{scale_y(y(d))}" for d in points))
        self.children = [renderer(d)]


class SvgScatterplot(HNode):
    def __init__(self, data, context, renderer, x=getter_x, y=getter_y):
        super().__init__(renderer=renderer)
        scale_x, scale_y = context["scale_x"], context["scale_y"]
        result = []
        for datum in data:
            sx = scale_x(x(datum))
            sy = scale_y(y(datum))
            result.append(f"M{sx} {sy} A0 0 0 0 1 {sx} {sy}")
        self.d = " ".join(result)
        self.children = [self.props["renderer"](self.d)]


class Point(HNode):
    def __str__(self):
        x, y = self.props["x"], self.props["y"]
        scale_x, scale_y = (
            self.props["context"]["scale_x"],
            self.props["context"]["scale_y"],
        )
        return h(
            "pancake-point",
            {"style": f"left: {scale_x(x)}%; top: {scale_y(y)}%"},
            self.children,
        )


DATA = [
    {"x": 0, "y": 0},
    {"x": 1, "y": 1},
    {"x": 2, "y": 4},
    {"x": 3, "y": 9},
    {"x": 4, "y": 16},
    {"x": 5, "y": 25},
    {"x": 6, "y": 36},
    {"x": 7, "y": 49},
    {"x": 8, "y": 64},
    {"x": 9, "y": 81},
    {"x": 10, "y": 100},
]


# fmt: off
def simple_chart():
    x, y = zip(*[(d["x"], d["y"]) for d in DATA])
    min_x, max_x = min(x), max(x)
    min_y, max_y = min(y), max(y)
    scale_x = linear([min_x, max_x], [0, 100])
    scale_y = linear([min_y, max_y], [100, 0])
    context = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "scale_x": scale_x,
        "scale_y": scale_y,
    }
    return HTag.div(className="chart", children=[
        Chart(children=[
            Box(
                children=[HTag.div(className='axes')],
            ),
            Grid(
                count=5,
                context=context,
                renderer=lambda value, **kwargs: [HTag.span(className="label x", children=[value])],
                vertical=True,
            ),
            Grid(
                count=2,
                context=context,
                renderer=lambda value, **kwargs: [HTag.span(className="label y", children=[value])],
                horizontal=True,
            ),
            HTag.svg(
                viewBox="0 0 100 100",
                preserveAspectRatio="none",
                children=[
                    SvgLine(
                        points=DATA,
                        context=context,
                        renderer=lambda d: HTag.path(className="data", d=d),
                    )
                ],
            )
        ])
    ])

# fmt: on


def chart():
    PPoint = namedtuple("PPoint", ["date", "avg", "trend"])
    with open("carbon.txt", "r") as f:
        points = [
            PPoint(float(date), float(avg), float(trend))
            for (date, avg, trend) in [line.strip().split("\t") for line in f]
            if avg != "-99.99"
        ]
    spoints = sorted(points, key=lambda p: p.avg)
    min_x = points[0].date
    max_x = points[-1].date
    min_y = spoints[0].avg
    max_y = spoints[-1].avg
    highest = spoints[-1]
    scale_x = linear([min_x, max_x], [0, 100])
    scale_y = linear([min_y, max_y], [100, 0])
    context = {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "scale_x": scale_x,
        "scale_y": scale_y,
    }

    # fmt: off
    return HTag.div(className='chart', children=[
        Chart(children=[
            Grid(
                count=5,
                context=context,
                renderer=lambda value, last, **kwargs: [
                    HTag.div(
                        className="grid-line horizontal",
                        children=[HTag.span(children=[f'{value}{" ppm" if last else ""}'])],
                    ),
                ],
                horizontal=True,
            ),
            Grid(
                count=5,
                context=context,
                renderer=lambda value, **kwargs: [
                    HTag.div(className='grid-line vertical'),
                    HTag.span(className="year-label", children=[value])
                ],
                vertical=True,
            ),
            HTag.svg(
                viewBox="0 0 100 100",
                preserveAspectRatio="none",
                children=[
                    SvgScatterplot(
                        points,
                        context=context,
                        renderer=lambda d: HTag.path(className='avg scatter', d=d),
                        x=lambda d: d.date,
                        y=lambda d: d.avg,
                    ),
                    SvgLine(
                        points=points,
                        context=context,
                        renderer=lambda d: HTag.path(className="avg", d=d),
                        x=lambda d: d.date,
                        y=lambda d: d.avg,
                    ),
                    SvgLine(
                        points=points,
                        context=context,
                        renderer=lambda d: HTag.path(className="trend", d=d),
                        x=lambda d: d.date,
                        y=lambda d: d.trend,
                    ),
                ],
            ),
            Point(
                context=context,
                x=1962,
                y=390,
                children=[
                    HTag.div(className='text', children=[
                        HTag.h2(children=["Atmospheric CO₂"]),
                        HTag.p(children=[
                            HTag.span(style="color: #676778", children=['•']),
                            HTag.span(children=['monthly average&nbsp;&nbsp;&nbsp;'], dangerousHTML=True),
                            HTag.span(style="color: #ff3e00", children=['—']),
                            HTag.span(children=['trend']),
                        ])
                    ]),
                ],
            ),
            Point(
                context=context,
                x=2015,
                y=330,
                children=[
                    HTag.div(className='text', style='right: 0; text-align: right;', children=[
                        HTag.p(children=[
                            HTag.em(children=['This chart will render correctly even if JavaScript is disabled.']),
                        ])
                    ]),
                ],
            ),
            Point(
                context=context,
                x=highest.date,
                y=highest.avg,
                children=[
                    HTag.div(
                        className='annotation',
                        style='position: absolute; right: 0.5em; top: -0.5em; white-space: nowrap; line-height: 1; color: #666;',
                        dangerousHTML=True,
                        children=[f'{highest.avg} parts per million (ppm) &rarr;'],
                    ),
                ],
            )
        ])
    ])
    # fmt: on


app = Flask(__name__)


# fmt: off
@app.route("/")
def index():
    return str(HTag.html(
        children=[
            HTag.head(children=[
                HTag.style(children=[style])
            ]),
            HTag.body(style="height: 100%; max-height: 400px", children=[
                HTag.h2(style='margin: 40px 0 0 40px', children=["Carbon Chart"]),
                chart(),
                HTag.h2(style='margin: 40px 0 0 40px', children=["Simple Chart"]),
                simple_chart(),
            ])
        ]
    ))
# fmt: on
