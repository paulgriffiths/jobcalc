"""
Provides a class for describing and drawing standard pipe flanges.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.


from jobcalc.helper import ptoc, Point
from math import pi


class Flange:

    """
    Flange class to hold standard flange dimensions.

    Public methods:
    __init__()
    draw()
    """

    dims = {"100PN16": (100, 220, 20, 180, 18, 8, 158, 2),
            "125PN16": (125, 250, 22, 210, 18, 8, 188, 2),
            "150PN16": (150, 285, 22, 240, 22, 8, 212, 2),
            "200PN16": (200, 340, 24, 295, 22, 12, 268, 2),
            "250PN16": (250, 405, 26, 355, 26, 12, 320, 2),
            "300PN16": (300, 460, 28, 410, 26, 12, 378, 2),
            "400PN16": (400, 580, 32, 525, 30, 16, 490, 2)}

    colors = {"section": (0.9, 0.9, 0.9),
              "line":   (0.0, 0.0, 0.0),
              "arc":    (1.0, 1.0, 1.0)}
    bolt_hole_line_size = 1.5

    def __init__(self, name):

        """
        Initializes a Flange instance.

        Arguments:
        name -- name of the flange
        """

        self.name = name
        self.hole_diameter = Flange.dims[name][0]
        self.flange_diameter = Flange.dims[name][1]
        self.flange_thickness = Flange.dims[name][2]
        self.bolt_circle_diameter = Flange.dims[name][3]
        self.bolt_hole_diameter = Flange.dims[name][4]
        self.num_bolts = Flange.dims[name][5]
        self.raised_face_diameter = Flange.dims[name][6]
        self.raised_face_height = Flange.dims[name][7]

    def draw(self, ctx, cfp=Point(0, 0), angle=0,
             profile=False, dash_style=None):

        """
        Draws a flange.

        Arguments:
        ctx -- a Pycairo context
        cfp -- Point instance for center end face of flange
        angle -- angle, in radians, at which to draw the flange. An
        angle of 0 is center end face of flange pointing directly
        downwards, with increasing angles rotating the flange counter
        clockwise
        profile -- set to True to draw the profile view in addition to
        the cross-section view
        dash_style -- the parent component's upscaled dash_style, for
        drawing the bolt hole circle
        """

        ctx.save()
        ctx.translate(*cfp.t())
        ctx.rotate(-angle)

        for reverse in [True, False]:
            self.draw_cross_section(ctx, reverse)

        if profile:
            self.draw_profile(ctx, dash_style)

        ctx.restore()

    def draw_cross_section(self, ctx, rev=False):

        """
        Draws a flange half cross section.

        Arguments:
        ctx -- a Pycairo context
        rev -- set to True to draw the reverse cross section half
        """

        rfr = self.raised_face_diameter / 2.0
        hrd = self.hole_diameter / 2.0
        frd = self.flange_diameter / 2.0
        fth = self.flange_thickness
        rfh = self.raised_face_height
        rev = -1 if rev else 1

        ctx.save()

        ctx.move_to(hrd * rev, 0)
        for cdx, cdy in [(rfr, 0), (rfr, rfh), (frd, rfh),
                         (frd, fth), (hrd, fth)]:
            ctx.line_to(cdx * rev, -cdy)
        ctx.close_path()

        ctx.set_source_rgb(*Flange.colors["section"])
        ctx.fill_preserve()
        ctx.set_source_rgb(*Flange.colors["line"])
        ctx.stroke()

        ctx.restore()

    def draw_profile(self, ctx, dash_style):

        """
        Draws the flange arcs, including bolt holes.

        Arguments:
        ctx -- a Pycairo context
        dash_style -- style of dashes to use to the bolt
        hole diameter
        """

        rfr = self.raised_face_diameter / 2.0
        hrd = self.hole_diameter / 2.0
        frd = self.flange_diameter / 2.0
        bcr = self.bolt_circle_diameter / 2.0
        bhr = self.bolt_hole_diameter / 2.0
        nbs = self.num_bolts / 2
        hls = Flange.bolt_hole_line_size

        ctx.save()

        # Draw flange arcs

        ctx.move_to(hrd, 0)
        ctx.line_to(frd, 0)
        ctx.arc(0, 0, frd, 0, pi)
        ctx.line_to(-hrd, 0)
        ctx.arc_negative(0, 0, hrd, pi, 0)
        ctx.close_path()

        ctx.set_source_rgb(*Flange.colors["arc"])
        ctx.fill_preserve()
        ctx.set_source_rgb(*Flange.colors["line"])
        ctx.stroke()

        ctx.arc(0, 0, rfr, 0, pi)
        ctx.stroke()

        # Draw bolt holes

        for i in range(nbs):
            ang = -pi / (nbs * 2) * (1 + i * 2)
            bhc = ptoc(ang, bcr)
            ctx.arc(bhc.x, bhc.y, bhr, 0, pi * 2)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill_preserve()

            ctx.set_source_rgb(*Flange.colors["line"])
            ctx.move_to(*ptoc(ang, bcr - bhr * hls).t())
            ctx.line_to(*ptoc(ang, bcr + bhr * hls).t())

            ctx.stroke()

        # Draw bolt hole circle arc

        if dash_style:
            ctx.set_dash(dash_style)
        ctx.arc(0, 0, bcr, 0, pi)
        ctx.stroke()

        # Extend center line arc to flange hole diameter

        ctx.move_to(0, 0)
        ctx.line_to(0, 0 + hrd)
        ctx.stroke()

        ctx.restore()
