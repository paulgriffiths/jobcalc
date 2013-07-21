"""
Provides a base class for pipe-based jobs.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.


from math import pi
from jobcalc.helper import ptoc, draw_dim_line
from jobcalc.flange import Flange
from jobcalc.component import DrawnComponent


class Pipe(DrawnComponent):

    """
    Pipe class to be used to automatically create a drawing.

    Public methods:
    __init__()
    """

    def __init__(self, casingod, casingid, liningod, liningid, flange):

        """
        Initializes a Pipe instance.

        Subclasses should call this at the beginning of their own
        constructor function.

        Arguments:
        casingod -- outside diameter of casing, in mm
        casingid -- inside diameter of casing, in mm
        liningod -- outside diameter of lining, in mm
        liningid -- inside diameter of lining, in mm
        flange -- name of flange
        """

        # Call superclass constructor

        DrawnComponent.__init__(self)

        # Properties common to all pipe components

        self.flange = Flange(flange)

        # Bend diameters and radii common to all pipe components

        self.diameters = {"co": casingod,
                          "ci": casingid,
                          "lo": liningod,
                          "li": liningid,
                          "fi": self.flange.hole_diameter,
                          "fo": self.flange.flange_diameter}

        self.p_rad = {"co": casingod / 2.0,
                      "ci": casingid / 2.0,
                      "lo": liningod / 2.0,
                      "li": liningid / 2.0,
                      "fi": self.flange.hole_diameter / 2.0,
                      "fo": self.flange.flange_diameter / 2.0}

        # Colors common to all pipe components

        comp_col = {"co": (0.8, 0.8, 0.8), "ci": (0.9, 0.9, 0.9),
                    "lo": (0.6, 0.6, 0.6), "li": (1.0, 1.0, 1.0)}
        self.colors = {"comp": comp_col}

    def set_scale(self, ctx, page_w, page_h):

        """
        Automatically sets a scale factor for the drawing.

        This will normally be called after the set_scale()
        function of a subclass has set the scale factor.
        'page_h' and 'page_w' should already have been up-scaled
        by the time this happens.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- height and width of the drawing area
        """

        # Upscale lines

        # Note that self.dim_line_length is used to calculate
        # the lengths of radius dimension lines. These lengths
        # can differ for individual subclasses, and so
        # self.dim_line_length should be set in the subclass's
        # own set_scale() function, but the dimension is common
        # to all Pipe subclasses, and so we upscale it here.

        self.dim_line_length /= self.scale     # pylint: disable=E1101

        # Call parent function

        DrawnComponent.set_scale(self, ctx, page_w, page_h)

    def draw_component(self, ctx, page_w, page_h):

        """
        Draws a core pipe component. Mainly calls supporting functions.

        This function is called by the 'component' base class. Subclasses
        should override this and call it at the beginning of their own
        draw_component() function, before providing further specific
        drawing functionality.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        # Draw the filled outer casing without an outline. Leaving
        # the overall outline until last, and drawing the other
        # segments with just side outlines, avoids drawing overlapping
        # lines across the bend face.

        self.draw_pipe_comp(ctx, "co", fill=True)
        self.draw_pipe_comp(ctx, "ci", fill=True, edges=True)
        self.draw_pipe_comp(ctx, "lo", fill=True, edges=True)
        self.draw_pipe_comp(ctx, "li", fill=True, edges=True)
        self.draw_pipe_comp(ctx, "co", outline=True)

        # Draw the other components

        self.draw_bend_profile(ctx)
        self.draw_rad_dims(ctx)
        self.draw_flanges(ctx)

    def draw_pipe_comp(self, ctx, comp, fill=False,
                       outline=False, edges=False):

        """
        Draws a segmented component of a bend.

        Arguments:
        ctx -- a Pycairo context
        comp -- type of component, "co", "ci", "lo" or "li"
        fill -- fills the component with color if True
        outline -- draws an outline around the entire component if True
        edges -- draws lines only along the segment edges if True
        """

        ctx.save()

        pts_out = self.pc_pts["out"][comp]     # pylint: disable=E1101
        pts_in = self.pc_pts["in"][comp]       # pylint: disable=E1101

        if fill or outline:
            pts = pts_out + pts_in
            for point in pts:
                if point is pts[0]:
                    ctx.move_to(*point.t())
                else:
                    ctx.line_to(*point.t())

            ctx.close_path()

            if fill:
                if comp == "co" and self.hatching:
                    ctx.set_source(self.chatch)
                elif comp == "lo" and self.hatching:
                    ctx.set_source(self.lhatch)
                else:
                    ctx.set_source_rgb(*self.colors["comp"][comp])

                if outline:
                    ctx.fill_preserve()
                else:
                    ctx.fill()

            if outline:
                ctx.set_source_rgb(*self.drawing_line_color)
                ctx.stroke()

        if edges:
            ctx.set_source_rgb(*self.drawing_line_color)
            for point in pts_out:
                if point is pts_out[0]:
                    ctx.move_to(*point.t())
                else:
                    ctx.line_to(*point.t())
            ctx.stroke()

            for point in pts_in:
                if point is pts_in[0]:
                    ctx.move_to(*point.t())
                else:
                    ctx.line_to(*point.t())
            ctx.stroke()

        ctx.restore()

    def draw_center_line(self, ctx):

        """
        Draws a dashed line along the center of the pipe.

        Note that this line will be segmented, not curved, for pipe bends.

        Arguments:
        ctx -- a Pycairo context
        """

        ctx.save()

        ctx.set_dash(self.dash_style)
        for point in self.pc_pts["ctr"]:          # pylint: disable=E1101
            if point == self.pc_pts["ctr"][0]:    # pylint: disable=E1101
                ctx.move_to(*point.t())
            else:
                ctx.line_to(*point.t())
        ctx.stroke()

        ctx.restore()

    def draw_rad_dims(self, ctx):

        """
        Draw the radius dimensions of the bend.

        Arguments:
        ctx -- a Pycairo context
        """

        # The angle at which the radius dimension lines are drawn
        # depends on the bend angle for pipe bends, but is always
        # vertical for pipe straights. Since this will be called
        # from a subclass, check whether we have a pipe bend by
        # verifying whether the "bend_arc" instance attribute is set.

        if hasattr(self, "bend_arc"):
            b_arc = self.bend_arc       # pylint: disable=E1101
        else:
            b_arc = 0

        pts = {}

        ctx.save()

        for scale, comp in zip(range(4, 0, -1), ["co", "ci", "lo", "li"]):

            # pylint: disable=E1101

            dll = self.dim_line_length * scale

            for i in ["out", "in"]:
                point = self.pc_pts[i][comp][-1 if i == "out" else 0]
                pts[i] = ptoc(b_arc + pi / 2, dll, point)
                ctx.move_to(*point.t())
                ctx.line_to(*pts[i].t())

            # pylint: enable=E1101

            ctx.stroke()
            draw_dim_line(ctx, pts["out"], pts["in"],
                          self.diameters[comp], self.scale, 0)

        ctx.restore()

    def draw_bend_profile(self, ctx):

        """
        Draws a half profile view of the pipe at the bottom.

        Arguments:
        ctx -- a Pycairo context
        """

        ctx.save()
        ctx.translate(self.pc_pts["ctr"][0].x,   # pylint: disable=E1101
                      self.pc_pts["ctr"][0].y)   # pylint: disable=E1101

        for rad in [self.p_rad[k] for k in ["li", "lo", "ci", "co"]]:
            ctx.arc(0, 0, rad, 0, pi)
        ctx.stroke()

        ctx.restore()

    def draw_flanges(self, ctx):

        """
        Draws the flanges.

        Arguments:
        ctx -- a Pycairo context
        """

        # The angle at which the upper flange is drawn
        # depends on the bend angle for pipe bends, but is always
        # horizontal for pipe straights. Since this will be called
        # from a subclass, check whether we have a pipe bend by
        # verifying whether the "bend_arc" instance attribute is set.

        # pylint: disable=E1101

        if hasattr(self, "bend_arc"):
            b_arc = self.bend_arc
        else:
            b_arc = 0

        self.flange.draw(ctx, cfp=self.pc_pts["ctr"][0], angle=0,
                         profile=True, dash_style=self.dash_style)
        self.flange.draw(ctx, cfp=self.pc_pts["ctr"][-1], angle=b_arc + pi,
                         profile=False)

        # pylint: enable=E1101
