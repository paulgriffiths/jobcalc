"""
Provides a class for pipe bend jobs.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.

# Disable pylint warnings for:
#  - too many arguments, possible future refactor
#  - too many local variables, possible future refactor
#  - too many instance attributes, possible future refactor
#
# pylint: disable=R0914
# pylint: disable=R0913
# pylint: disable=R0902


from math import pi, radians, sin, cos, tan
from jobcalc.helper import ptoc, Point, LabeledValue, draw_text_box
from jobcalc.helper import draw_dim_label, draw_dim_line, draw_arrowhead
from jobcalc.helper import get_largest_text_width
from jobcalc.pipe import Pipe


class PipeBend(Pipe):

    """
    PipeBend class to be used to automatically create a bend drawing.

    Public methods:
    __init__()
    """

    def __init__(self, nomrad, casingod, casingid, liningod,
                 liningid, bendangle, segangle, ctype, flange,
                 exdimdrg, exdimbox):

        """
        Initializes a PipeBend instance.

        Arguments:
        nomrad -- nominal radius, in mm
        casingod -- outside diameter of casing, in mm
        casingid -- inside diameter of casing, in mm
        liningod -- outside diameter of lining, in mm
        liningid -- inside diameter of lining, in mm
        bendangle -- angle, in degrees, of overall bend
        segangle -- angle, in degrees, of each bend segment
        ctype -- type of casing, either "onepiece" or "segmented"
        exdimdrg -- True to show segment dimensions on main drawing
        exdimbox -- True to show segment dimensions in an infobox
        """

        # Call superclass constructor

        Pipe.__init__(self, casingod, casingid, liningod, liningid, flange)

        # Page dimensions and properties

        self.dos_dim_line_length = 30
        self.dos_dim_dp = 3

        # Bend angles, properties and information

        self.bend_arc_d = bendangle
        self.segment_angle_d = segangle
        self.bend_arc = radians(bendangle)
        self.segment_angle = radians(segangle)
        self.num_segments = int(self.bend_arc / self.segment_angle)
        self.casing_type = ctype
        self.ex_dim_box = exdimbox
        self.ex_dim_drg = exdimdrg

        # Bend diameters and radii

        fod = self.flange.flange_diameter

        self.diameters["nom"] = nomrad * 2

        outer_radii = {"nom": nomrad,
                       "co": nomrad + casingod / 2.0,
                       "ci": nomrad + casingid / 2.0,
                       "lo": nomrad + liningod / 2.0,
                       "li": nomrad + liningid / 2.0,
                       "fo": nomrad + fod / 2.0}
        inner_radii = {"nom": nomrad,
                       "co": nomrad - casingod / 2.0,
                       "ci": nomrad - casingid / 2.0,
                       "lo": nomrad - liningod / 2.0,
                       "li": nomrad - liningid / 2.0,
                       "fo": nomrad - fod / 2.0}
        self.radii = {"inner": inner_radii,
                      "outer": outer_radii,
                      "nom": nomrad}

        # Calculate and store segment dimensions

        # pylint: disable=C0103

        self.segdims = {}
        for k, i, d, l in zip(["cex", "cin", "lex", "lin", "mean"],
                              ["outer", "inner", "outer", "inner", "outer"],
                              ["co", "co", "lo", "lo", "nom"],
                              ["Casing seg. extra. length",
                               "Casing seg. intra. length",
                               "Lining seg. extra. length",
                               "Lining seg. intra. length",
                               "Mean seg. length"]):
            dim = self.radii[i][d] * tan(self.segment_angle / 2) * 2
            self.segdims[k] = LabeledValue(l, dim)

        # pylint: enable=C0103

        # Calculate segmented component points

        pc_pts_out = {}
        pc_pts_in = {}

        for k in ["co", "ci", "lo", "li"]:
            pc_pts_out[k] = self.get_segment_points(self.radii["outer"][k])
            pc_pts_in[k] = self.get_segment_points(self.radii["inner"][k])
            pc_pts_in[k].reverse()
        pc_pts_ctr = self.get_segment_points(self.radii["nom"])
        self.pc_pts = {"in": pc_pts_in, "out": pc_pts_out,
                       "ctr": pc_pts_ctr}

    def get_segment_points(self, rad):

        """
        Calculates coordinates for segment vertices at a specified radius.
        """

        # Note that the nominal radius of the bend is calculated to the
        # center of the segment at its mid-point, not at its end. If this
        # were not so, the midpoint of the bend ends would not align with the
        # nominal radius, as the bend is always ended with half segments.
        # Since we are calculating coordinates for the segment vertices
        # at the ends, and not for the mid-points, we cannot use the
        # nominal radius to do this. Instead, we use the 'erad' variable
        # which calculates the radius we need to use for the segment
        # vertices that will cause the segment mid-points to align
        # with the nominal radius.

        # Contrast this with calculating the segment intrados and
        # extrados lengths, in the class initializer, where we do
        # use the nominal radius, but calculate a tangent. This
        # is not available here due to the ptoc() function needing
        # a radius to the end points, rather than to the mid point.

        pts = []
        s_ang = self.segment_angle
        b_arc = self.bend_arc
        erad = rad / cos(s_ang / 2)

        pts.append(ptoc(0, rad))
        for ang in [n + 0.5 for n in range(self.num_segments)]:
            pts.append(ptoc(s_ang * ang, erad))
        pts.append(ptoc(b_arc, rad))

        return pts

    def draw_pre_scale(self, ctx, page_w, page_h):

        """
        Override superclass to draw segment dimensions box.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area.
        """

        self.draw_seg_dims_box(ctx, page_w, page_h)

    def draw_component(self, ctx, page_w, page_h):

        """
        Draws a bend. Mainly calls supporting functions.

        This function is called by the 'component' base class.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        # Call the superclass function...

        Pipe.draw_component(self, ctx, page_w, page_h)

        # ...and then provide bend-specific drawing functionality.

        self.draw_ribs(ctx, "li")
        self.draw_center_arc(ctx)
        self.draw_arc_dims(ctx)
        if self.ex_dim_drg:
            self.draw_seg_dims(ctx)

    def draw_pipe_comp(self, ctx, comp, fill=False,
                       outline=False, edges=False):

        """
        Intercepts the superclass function to provide for curved casings.
        """

        if self.casing_type == "onepiece" and comp[0] == "c":
            self.draw_curved_bend(ctx, comp, fill=fill,
                                  outline=outline, edges=edges)
        else:
            Pipe.draw_pipe_comp(self, ctx, comp, fill=fill,
                                outline=outline, edges=edges)

    def set_scale(self, ctx, page_w, page_h):

        """
        Automatically sets a scale factor for the bend drawing.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        b_arc = self.bend_arc
        cri = self.radii["inner"]["co"]
        cro = self.radii["outer"]["co"]
        bfr = self.radii["outer"]["fo"]
        flr = self.p_rad["fo"]

        # Calculate segment dimension line lengths

        dim_values = []
        dpt = self.dos_dim_dp
        for dim in ["cex", "cin", "lex", "lin"]:
            dim_values.append(str(round(self.segdims[dim].value, dpt)))
        ddm = get_largest_text_width(ctx, dim_values, self.text["dims"], True)
        self.dos_dim_line_length = ddm

        # Calculate radius dimension line lengths, these vary based
        # on font size, and need to be considered for scaling along
        # the axes. These dimensions will be upscaled during the
        # final drawing, and will be independent of the scale factor
        # calculated.

        rad_values = []
        for comp in ["co", "ci", "lo", "li"]:
            rad_values.append(str(int(round(self.diameters[comp]))))
        rdm = get_largest_text_width(ctx, rad_values, self.text["dims"], True)
        self.dim_line_length = rdm
        rdm = self.dim_line_length * 4

        # Calculate x scale factor

        # dos_s not yet implemented. Under some circumstances the segment
        # dimension lines on the drawing can extend past the right edge
        # of the drawing extent currently calculated here. The option to
        # suppress the dimension lines and relegate them to a box is
        # available, so problem is minor. Scaling depends upon whether
        # casing is one-piece of segments, whether the option to show
        # the segment dimensions was shown, and so on, so is more
        # complicated than the options shown here. Approach should be
        # the same, calculate the width including the segment dimension
        # lines under the selected options, and then scale based on that
        # if it turns out to be the largest of the calculated width. Then
        # set the x origin accordingly.

        #n      = ns//2 + (ns%2)
        #dx     = ptoc(sa*n,ddm*1.5).x
        #pt     = self.pc_pts["out"]["co"][n]
        #dos_w  = pt.x

        rad_w = bfr
        ang_w = rad_w - cos(b_arc) * cri
        dm_w = cos(pi / 2 - b_arc) * rdm

        #dos_s  = (page_w - dx) / dos_w

        rad_s = page_w / bfr
        ang_s = (page_w - dm_w) / ang_w
        x_scale = min(rad_s, ang_s)

        # Calculate y scale factor

        rad_h = sin(b_arc) * bfr + flr
        ang_h = sin(b_arc) * cro + flr
        dm_h = sin(pi / 2 - b_arc) * rdm
        y_scale = min(page_h / rad_h, (page_h - dm_h) / ang_h)

        # Set scale based on smallest factor

        self.scale = min(x_scale, y_scale)
        ctx.scale(self.scale, self.scale)

        # Set bend origin based on calculated scale

        page_w /= self.scale
        bend_w = max(rad_w, ang_w + dm_w / self.scale)
        x_origin = page_w - (page_w - bend_w) / 2 - bfr

        page_h /= self.scale
        bend_h = max(rad_h, ang_h + dm_h / self.scale)
        y_origin = page_h - (page_h - bend_h) / 2 - flr

        ctx.translate(x_origin, y_origin)

        # Scale lines

        self.dos_dim_line_length /= self.scale

        # Call superclass function

        Pipe.set_scale(self, ctx, page_w, page_h)

    def draw_ribs(self, ctx, comp):

        """
        Draws internal ribs for segmented bend component.

        Arguments:
        ctx -- a Pycairo context
        comp -- type of component, "co", "ci", "lo" or "li"
        """

        ctx.save()

        pts_out = self.pc_pts["out"][comp]
        pts_in = self.pc_pts["in"][comp]

        for pt1, pt2 in zip(pts_out[1:-1], pts_in[-2:0:-1]):
            ctx.move_to(*pt1.t())
            ctx.line_to(*pt2.t())
        ctx.stroke()

        ctx.restore()

    def draw_curved_bend(self, ctx, comp, fill=False,
                         edges=False, outline=False):

        """
        Draws a smoothly curved (not segmented) bend component.

        Arguments:
        ctx -- a Pycairo context
        comp -- type of component, "co", "ci", "lo" or "li"
        outline -- draws an outline around the entire component if True.
        """

        b_arc = self.bend_arc
        rads = self.radii

        ctx.save()

        if fill or outline:
            ctx.move_to(*ptoc(0, rads["inner"][comp]).t())
            ctx.line_to(*ptoc(0, rads["outer"][comp]).t())
            ctx.arc_negative(0, 0, rads["outer"][comp], 0, pi * 2 - b_arc)
            ctx.line_to(*ptoc(b_arc, rads["inner"][comp]).t())
            ctx.arc(0, 0, rads["inner"][comp], pi * 2 - b_arc, 0)
            ctx.close_path()

            if fill:
                if comp == "co" and self.hatching:
                    ctx.set_source(self.chatch)
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

            for i in ["outer", "inner"]:
                ctx.arc(0, 0, rads[i][comp], pi * 2 - b_arc, 0)
                ctx.stroke()

        ctx.restore()

    def draw_center_arc(self, ctx):

        """
        Draws a dashed arc along the nominal radius of the bend.

        Arguments:
        ctx -- a Pycairo context
        """

        ctx.save()

        ctx.set_dash(self.dash_style)
        ctx.arc(0, 0, self.radii["nom"], pi * 2 - self.bend_arc, 0)
        ctx.stroke()

        ctx.restore()

    def draw_arc_dims(self, ctx):

        """
        Draws dimensions for a bend arc and radius.

        ctx -- a Pycairo context
        """

        b_arc = self.bend_arc
        s_ang = self.segment_angle
        rad = self.radii["inner"]["fo"] * 0.95

        ctx.save()

        # Draw angle lines to origin

        ctx.move_to(*ptoc(b_arc, rad).t())
        ctx.line_to(0, 0)
        ctx.line_to(rad, 0)
        ctx.stroke()

        # Draw angle arc and dimension label

        rad /= 3

        ctx.arc(0, 0, rad, pi * 2 - b_arc, 0)
        ctx.stroke()

        draw_arrowhead(ctx, b_arc + pi / 2, ptoc(b_arc, rad), self.scale)
        draw_arrowhead(ctx, pi * 3 / 2, ptoc(0, rad), self.scale)
        draw_dim_label(ctx, ptoc(b_arc / 2, rad),
                       self.bend_arc_d, self.scale, 0, "d")

        # Draw nominal radius dimension line and label

        rad *= 2
        if self.num_segments % 2:
            angle = b_arc / 2 + s_ang / 2
        else:
            angle = b_arc / 2

        pt1 = ptoc(angle, rad)
        pt2 = ptoc(angle, self.radii["nom"])
        ctx.move_to(*pt1.t())
        ctx.line_to(*pt2.t())
        ctx.stroke()
        draw_arrowhead(ctx, angle, pt2, self.scale)
        draw_dim_label(ctx, pt1, self.radii["nom"], self.scale, 0, "r")

        ctx.restore()

    def draw_seg_dims(self, ctx):

        """
        Draw segment extrados and intrados dimensions.

        Arguments:
        ctx -- a Pycairo context
        """

        segs = self.num_segments
        s_ang = self.segment_angle
        cld = self.p_rad["co"] - self.p_rad["lo"]
        dpt = self.dos_dim_dp
        ddll = self.dos_dim_line_length

        idx = [0, 0]
        pts = [0, 0]

        ctx.save()

        if segs >= 3:

            # Draw extrados dimensions

            idx[0] = segs // 2 + (segs % 2)
            idx[1] = idx[0] + 1

            for comp, dim in zip(["co", "lo"],
                           [self.segdims[k].value for k in ["cex", "lex"]]):
                if comp == "co" and self.casing_type == "onepiece":
                    continue
                for line in range(2):
                    stp = self.pc_pts["out"][comp][idx[line]]
                    lnl = ddll * 1.7 if comp == "co" else cld + ddll * 0.7
                    pts[line] = ptoc(s_ang * idx[0], lnl, stp)

                    ctx.move_to(*stp.t())
                    ctx.line_to(*pts[line].t())

                ctx.stroke()
                draw_dim_line(ctx, pts[1], pts[0], dim, self.scale, dpt)

            # Draw intrados dimensions

            idx[0] += 1 - (segs % 2)
            idx[1] = idx[0] + 1

            for comp, dim in zip(["co", "lo"],
                            [self.segdims[k].value for k in ["cin", "lin"]]):
                if comp == "co" and self.casing_type == "onepiece":
                    continue
                for line in range(2):
                    if self.casing_type == "onepiece":
                        mult = 0.7
                    else:
                        mult = 1.7
                    stp = self.pc_pts["in"][comp][idx[line]]
                    lnl = ddll * 0.7 if comp == "co" else cld + ddll * mult
                    pts[line] = ptoc(s_ang * (idx[0] - 2 + segs % 2) +
                                     pi, lnl, stp)

                    ctx.move_to(*stp.t())
                    ctx.line_to(*pts[line].t())

                ctx.stroke()
                draw_dim_line(ctx, pts[1], pts[0], dim, self.scale, dpt)

        ctx.restore()

    # pylint: disable=W0613

    def draw_seg_dims_box(self, ctx, page_w, page_h):

        """
        Draws an info box containing bend segment dimensions.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of the drawing area
        """

        # Draw segment dimensions box

        ctx.set_line_width(self.drawing_line_width)

        if self.ex_dim_box or self.ex_dim_drg:
            if not self.ex_dim_box:
                dims = ["mean"]
            elif self.casing_type == "segmented":
                dims = ["cex", "lex", "mean", "lin", "cin"]
            else:
                dims = ["lex", "mean", "lin"]

            dpt = self.dos_dim_dp
            labels, fields = zip(*[(self.segdims[k].label,
                                    str(round(self.segdims[k].value, dpt)))
                                   for k in dims])

            draw_text_box(ctx=ctx, topright=Point(page_w, 0),
                          labels=labels, fields=fields,
                          textinfo=self.text["dims"])

    # pylint: enable=W0613
