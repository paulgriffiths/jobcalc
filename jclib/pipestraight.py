"""
Provides a class for pipe straight jobs.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.


from jobcalc.helper import Point, get_largest_text_height
from jobcalc.helper import get_largest_text_width, draw_dim_line
from jobcalc.pipe import Pipe


class PipeStraight(Pipe):

    """
    PipeStraight class to be used to automatically create a bend drawing.

    Public methods:
    __init__()
    """

    def __init__(self, length, casingod, casingid, liningod, liningid, flange):

        """
        Initializes a PipeStraight instance.

        Arguments:
        length -- length of straight, in mm
        casingod -- outside diameter of casing, in mm
        casingid -- inside diameter of casing, in mm
        liningod -- outside diameter of lining, in mm
        liningid -- inside diameter of lining, in mm
        """

        # Call superclass constructor

        Pipe.__init__(self, casingod, casingid, liningod, liningid, flange)

        # Straight properties

        self.length = length
        self.len_dim_line_length = 0
        self.len_dim_line_length_offset_m = 1
        self.len_dim_line_length_width_m = 2

        # Calculate straight component points

        pc_pts_out = {}
        pc_pts_in = {}
        pc_pts_ctr = []

        for comp in ["co", "ci", "lo", "li"]:
            pc_pts_out[comp] = []
            pc_pts_in[comp] = []
            for y in [0, -self.length]:
                pc_pts_out[comp].append(Point(self.p_rad[comp], y))
                pc_pts_in[comp].append(Point(-self.p_rad[comp], y))
            pc_pts_in[comp].reverse()

        for y in [0, -self.length]:
            pc_pts_ctr.append(Point(0, y))

        self.pc_pts = {"in": pc_pts_in, "out": pc_pts_out,
                       "ctr": pc_pts_ctr}

    def draw_component(self, ctx, page_w, page_h):

        """
        Draws a straight. Mainly calls supporting functions.

        This function is called by the 'component' base class.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        # Call the parent function...

        Pipe.draw_component(self, ctx, page_w, page_h)

        # ...and then provide straight-specific drawing functionality.

        self.draw_center_line(ctx)
        self.draw_len_dim(ctx)

    def set_scale(self, ctx, page_w, page_h):

        """
        Automatically sets a scale factor for the straight drawing.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        pipelen = self.length
        fld = self.diameters["fo"]
        flr = self.p_rad["fo"]

        # Calculate radius dimension line lengths, these vary based
        # on font size, and need to be considered for scaling along
        # the y-axis. These dimensions will be upscaled during the
        # final drawing, and will be independent of the scale factor
        # calculated.

        rad_values = []
        for comp in ["co", "ci", "lo", "li"]:
            rad_values.append(str(int(round(self.diameters[comp]))))
        rdm = get_largest_text_height(ctx, rad_values, self.text["dims"], True)
        self.dim_line_length = rdm
        rdm = self.dim_line_length * 4

        # Calculate length dimension width, this can vary based both
        # on font size and on the length itself, and needs to be
        # considered for scaling along the x-axis. This dimension will
        # be upscaled during the final drawing, and will be independent
        # of the scale factor calculated.

        len_values = []
        len_values.append(str(int(round(self.length))))
        ldm = get_largest_text_width(ctx, len_values, self.text["dims"], True)
        self.len_dim_line_length = ldm
        ldm *= (self.len_dim_line_length_offset_m +
                self.len_dim_line_length_width_m)

        # Calculate x and y scale factors

        x_scale = (page_w - ldm) / fld
        y_scale = (page_h - rdm) / (pipelen + flr)

        # Scale based on the smallest factor

        self.scale = min(x_scale, y_scale)
        ctx.scale(self.scale, self.scale)

        # Set the origin based on calculated scale

        page_w /= self.scale
        bend_w = fld + ldm / self.scale
        x_origin = (page_w - bend_w) / 2 + flr

        page_h /= self.scale
        bend_h = pipelen + flr + rdm / self.scale
        y_origin = page_h - (page_h - bend_h) / 2 - flr

        ctx.translate(x_origin, y_origin)

        # Upscale line lengths

        self.len_dim_line_length /= self.scale

        # Call superclass function

        Pipe.set_scale(self, ctx, page_w, page_h)

    def draw_len_dim(self, ctx):

        """
        Draws the length dimension line for a straight.

        Arguments:
        ctx -- a Pycairo context
        """

        ldm = self.len_dim_line_length
        lom = self.len_dim_line_length_offset_m
        lwm = self.len_dim_line_length_width_m
        lem = lom + lwm
        lcm = lom + lwm / 2

        pts = []
        for end in [0, -1]:
            pts.append(self.pc_pts["ctr"][end])

        ctx.save()

        # Draw the bounding lines

        for num in range(2):
            ctx.move_to(self.p_rad["fo"] + ldm * lom, pts[num].y)
            ctx.line_to(self.p_rad["fo"] + ldm * lem, pts[num].y)
            ctx.stroke()

        # Draw the dimension line itself

        for num in range(2):
            pts[num] = Point(self.p_rad["fo"] + ldm * lcm, pts[num].y)

        draw_dim_line(ctx, pts[0], pts[1], self.length, self.scale, 0, "")

        ctx.restore()
