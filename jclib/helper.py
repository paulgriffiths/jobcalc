"""
Provides some helper classes and functions for JobCalc.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.

# Disable pylint warnings for:
#  - short variable names, as they are commonly used in this module
#  - too few public methods, intentional for helper classes
#  - too many arguments, a potential future refactor
#  - too many local variables, another potential future refactor
#
# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0913
# pylint: disable=R0914


from math import pi, sin, cos, atan, sqrt
import cairo
import sys


##############################
#
# Helper classes
#


class LabeledValue:

    """
    Class to hold a value with an associated label.

    Public methods:
    __init()__
    """

    def __init__(self, label, value):

        """
        Initializes a LabeledValue instance.
        """

        self.label = label
        self.value = value


class TextInfo:

    """
    Class to hold text font and padding information.

    Public methods:
    __init()__
    """

    def __init__(self, face="Arial", bold=False,
                 size=8, padding=3, color=(0, 0, 0)):

        """
        Initializes a TextInfo instance.
        """

        self.face = (face, cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        self.size = size
        self.padding = padding
        self.color = color


class Point:

    """
    Class to hold a cartesian coordinate.

    Public methods:
    __init__()
    t()
    """

    def __init__(self, x, y):

        """
        Initializes a Point instance.
        """

        self.x = x
        self.y = y

    def t(self):

        """
        Returns the coordinates as a tuple.

        Provided so that the coordinates can be unpacked using the
        '*' operator and passed to a function expecting two
        arguments.
        """

        return (self.x, self.y)


##############################
#
# Helper functions
#


def xnor(a, b):

    """
    Logical XNOR function, since Python does not
    provide by default.
    """

    return bool(a) == bool(b)


def ptoc(theta, r, p=Point(0, 0)):

    """
    Returns cartesian coordinates for polar coordinates.

    Note: as normal for graphics, this assumes an inverse y-axis
    compared to regular cartesian coordinates, i.e. y increases
    in the downwards rather than upwards direction.

    Arguments:
    theta -- theta coordinate, in radians, 0 is right along the x-axis,
    with angles increasing counter-clockwise.
    r -- r coordinate.
    p -- optional Point instance coordinates for the origin, default to zero.
    """

    return Point(p.x + cos(theta) * r, p.y - sin(theta) * r)


def get_largest_text_width(ctx, labels, ti, padding=False):

    """
    Returns the longest width in a list of text labels.

    Arguments:
    ctx -- a Pycairo context
    labels -- list of strings containing the labels
    ti -- a TextInfo instance with text information
    padding -- set to True to including padding in the returned width
    """

    ctx.save()
    ctx.select_font_face(*ti.face)
    ctx.set_font_size(ti.size)

    max_w = 0

    # pylint: disable=W0612

    for l in labels:
        (bx, by, w, h, dx, dy) = ctx.text_extents(l)
        if w > max_w:
            max_w = w

    # pylint: enable=W0612

    ctx.restore()

    if padding:
        max_w += ti.padding * 2

    return max_w


def get_largest_text_height(ctx, labels, ti, padding=False):

    """
    Returns the largest height in a list of text labels.

    Arguments:
    ctx -- a Pycairo context
    labels -- list of strings containing the labels
    ti -- a TextInfo instance with text information
    padding -- set to True to include padding in the returned height
    """

    ctx.save()
    ctx.select_font_face(*ti.face)
    ctx.set_font_size(ti.size)

    max_h = 0

    # pylint: disable=W0612

    for l in labels:
        (bx, by, w, h, dx, dy) = ctx.text_extents(l)
        if h > max_h:
            max_h = h

    # pylint: enable=W0612

    ctx.restore()

    if padding:
        max_h += ti.padding * 2

    return max_h


def draw_arrowhead(ctx, angle, p, scale, l=8, w=4):

    """
    Draws an arrowhead at a specified point and angle.

    Arguments:
    ctx -- a Pycairo context
    p -- Point instance for the tip of the arrowhead
    angle -- angle in radians in which the arrowhead is to point, with
    0 being right along the x-axis, angles increasing counter-clockwise.
    scale -- scale factor, to ensure arrowheads remain same size
    l -- default length of the arrowhead, along the notional line
    w -- default width of the arrowhead at the base.
    """

    ctx.save()

    l /= scale
    w /= scale
    h = sqrt((l ** 2) + ((w / 2.0) ** 2))
    a_offset = atan((w / 2.0) / l)

    ctx.set_source_rgb(0, 0, 0)
    ctx.move_to(*p.t())
    for offset in [a_offset, -a_offset]:
        ctx.line_to(*ptoc(angle + pi + offset, h, p).t())
    ctx.close_path()
    ctx.fill()

    ctx.restore()


def draw_dim_line(ctx, ps, pe, dim, scale, dp=0, opt=""):

    """
    Draws a labelled dimension line between two points.

    The label is centered at the geometric center of the line.
    Arrowheads are placed at either end of the line.

    Arguments:
    ctx -- a Pycairo context
    ps, pe -- starting and ending Point instances for line
    dp -- number of decimal places
    dim -- numeric dimension for the label.
    scale -- scale factor, used for dimension lines
    opt -- passed to draw_dim_label, "R" for radius, "D" for degree sign
    """

    ctx.save()

    # Draw the dimension line

    ctx.move_to(*ps.t())
    ctx.line_to(*pe.t())
    ctx.stroke()

    # Draw the arrowheads, and watch for division by zero

    try:
        angle = atan((pe.y - ps.y) / (ps.x - pe.x))
    except ZeroDivisionError:

        # Tangents repeat every 180 degrees, so we have a bit
        # more work to do to figure out at which angles to draw
        # the arrowheads.

        if ps.y < pe.y:
            angle = pi / 2
        else:
            angle = pi * 3 / 2

    # Similarly, calculate an adjusting factor for the arrowhead
    # angle because we calculated it using a tangent.

    a = [1, 0] if pe.x > ps.x else [0, 1]

    # Draw the arrowheads

    for o, p in zip(a, [ps, pe]):
        draw_arrowhead(ctx, angle + pi * o, p, scale)

    # Draw the label

    p = Point((ps.x + pe.x) / 2.0, (ps.y + pe.y) / 2.0)
    draw_dim_label(ctx, p, dim, scale, dp, opt)

    ctx.restore()


def draw_dim_label(ctx, p, dim, scale, dp=0, opt=""):

    """
    Draws a dimension label with a whitespace box at a specified point.

    Arguments:
    ctx -- a Pycairo context
    p -- Point instance for center of label
    dim -- numeric dimension for the label
    scale -- scale factor
    dp -- number of decimal places
    opt -- "r" to add a radius symbol, "d" to add a degree symbol.
    """

    margin = 3 / scale
    font_face = "Arial"
    font_size = 8.0 / scale

    ctx.save()
    ctx.translate(*p.t())

    dim_str = str(int(dim)) if dp == 0 else str(round(dim, dp))

    if opt.upper() == "R":
        dim_str = "R" + dim_str

    # Get text extents for dimension label

    ctx.select_font_face(font_face, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(font_size)

    # pylint: disable=W0612

    (bx, by, w, h, dx, dy) = ctx.text_extents(dim_str)

    # pylint: enable=W0612

    hw = w / 2
    hh = h / 2

    # Clear some whitespace for the dimension label

    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0 - hw - margin, 0 - hh - margin,
                  w + margin * 2, h + margin * 2)
    ctx.fill()

    # Draw the dimension label

    ctx.set_source_rgb(0, 0, 0)
    ctx.move_to(0 - hw, hh)
    ctx.show_text(dim_str)

    if opt.upper() == "D":
        ctx.set_font_size(font_size / 1.7)
        deg_str = "o"
        (bx, by, w, h, dx, dy) = ctx.text_extents(deg_str)
        ctx.move_to(hw + margin / 2, h - hh)
        ctx.show_text(deg_str)

    ctx.stroke()

    ctx.restore()


def draw_text_box(ctx, textinfo, labels, topleft=None, topright=None,
                  bottomleft=None, bottomright=None, centerpoint=None,
                  width=None, fields=None, center=False, noborder=False):

    """
    Constructs a multi-row info box contains labels and values.

    Arguments:
    textinfo -- TextInfo instance to use for the box and text
    labels -- list containing the labels
    topleft, topright, bottomleft, bottomright, centerpoint -- contains
    the Point instance of the relevant corner, only one of these should
    be passed to the function.
    width -- width of box, if a fixed width box is desired
    fields -- list containing the values, optional if each row
    contains a single string
    center -- set to True to center the text in the box.
    noborder -- set to True to not draw a border around the box
    """

    ctx.save()

    ctx.select_font_face(*textinfo.face)
    ctx.set_font_size(textinfo.size)

    label_w, field_w, row_h = 0, 0, 0
    nl = len(labels)
    ifm = textinfo.padding
    fps = []

    # Calculate width and height of largest label

    for l in labels:

        # pylint: disable=W0612

        (bx, by, w, h, dx, dy) = ctx.text_extents(l)

        # pylint: enable=W0612

        if w > label_w:
            label_w = w
        if h > row_h:
            row_h = h

    if fields:
        for f in fields:
            (bx, by, w, h, dx, dy) = ctx.text_extents(f)
            if w > field_w:
                field_w = w
            if h > row_h:
                row_h = h

    row_h += ifm * 2
    label_w += ifm * 2
    field_w += ifm * 2
    box_h = row_h * nl

    if width:
        box_w = width
    else:
        box_w = label_w + field_w

    if bottomleft:
        ctx.translate(bottomleft.x, bottomleft.y - box_h)
    elif bottomright:
        ctx.translate(bottomright.x - box_w, bottomright.y - box_h)
    elif topright:
        ctx.translate(topright.x - box_w, topright.y)
    elif topleft:
        ctx.translate(topleft.x, topleft.y)
    elif centerpoint:
        ctx.translate(centerpoint.x - label_w / 2,
                      centerpoint.y - row_h / 2)

    if not noborder:
        ctx.rectangle(0, 0, box_w, box_h)

    # Draw line dividing labels and fields

    if fields and not noborder:
        ctx.move_to(label_w, 0)
        ctx.line_to(label_w, box_h)

    ctx.stroke()

    # Draw labels and values

    for i in range(nl):
        y = row_h * (i + 1)
        if i < (nl - 1):
            ctx.set_source_rgb(0, 0, 0)
            ctx.move_to(0, y)
            ctx.line_to(box_w, y)
            ctx.stroke()
        (bx, by, w, h, dx, dy) = ctx.text_extents(labels[i])
        y -= ifm

        # Centering currently only works for boxes without
        # fields, as label width is only bigger than necessary
        # with a fixed width for the entire box, investigate
        # alternative solution

        if center:
            x = (box_w - w) / 2
        else:
            x = ifm

        ctx.move_to(x, y)
        ctx.set_source_rgb(*textinfo.color)
        ctx.show_text(labels[i])

        if fields:
            x += label_w
            (fx, fy) = ctx.user_to_device(x, y)
            fps.append(Point(fx, fy))
            ctx.move_to(x, y)
            ctx.show_text(fields[i])

    ctx.restore()

    return (box_w, box_h, fps)


def html_fail(msg):

    """
    Function to print basic HTML fallback page on error.

    Arguments:
    msg -- string of error message to output.
    """

    print("Content-type: text/html\n")

    print("<html>\n<head><title>Error!</title></head>\n")
    print("<body><h1>Error!</h1>\n")
    print("<p>%s</p>\n" % msg)
    print("</body>\n</html>\n")

    sys.exit()
