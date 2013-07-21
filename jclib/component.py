"""
Defines a base class for drawn jobs.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# All rights reserved.


import cairo
from jobcalc.helper import draw_text_box, Point, TextInfo


class DrawnComponent:

    """
    DrawnComponent class to be used to automatically create a drawing.

    This is a base class from which classes for specific components
    should inherit. Instances of this class are not intended to be
    directly drawn.

    Public methods:
    __init__()
    draw()
    """

    def __init__(self):

        """
        Initializes a DrawnComponent instance.

        Subclasses should call this at the beginning of their
        own constructor function.
        """

        # Drawing attributes

        self.scale = 1
        self.drawing_line_width = 0.5
        self.drawing_line_color = (0, 0, 0)
        self.hatching = False

        # Text objects and styles common to all components

        self.dash_style = [7.0, 2.0, 2.0, 2.0]

        self.text = {"dims": TextInfo(face="Arial", size=8,
                                      padding=3, color=(0.0, 0.0, 0.0)),
                     "info": TextInfo(face="Arial", size=8,
                                      padding=3, color=(0.0, 0.0, 0.0)),
                     "notice": TextInfo(face="Arial", size=10,
                                        padding=3, color=(0.0, 0.0, 0.0))}

        # Create Pycairo hatching patterns

        if self.hatching:
            chatch = cairo.ImageSurface(cairo.FORMAT_RGB24, 10, 10)
            ctx = cairo.Context(chatch)
            ctx.set_source_rgb(1, 1, 1)
            ctx.paint()
            ctx.set_source_rgb(0, 0, 0)
            ctx.set_line_width(1)
            ctx.move_to(0, 10)
            ctx.line_to(10, 0)
            ctx.stroke()
            self.chatch = cairo.SurfacePattern(chatch)

            lhatch = cairo.ImageSurface(cairo.FORMAT_RGB24, 10, 10)
            ctx = cairo.Context(lhatch)
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()
            ctx.set_source_rgb(1, 1, 1)
            ctx.set_line_width(1)
            ctx.move_to(0, 10)
            ctx.line_to(10, 0)
            ctx.move_to(0, 9)
            ctx.line_to(9, 0)
            ctx.move_to(1, 10)
            ctx.line_to(10, 1)
            ctx.move_to(0, 1)
            ctx.line_to(1, 0)
            ctx.move_to(9, 10)
            ctx.line_to(10, 9)
            ctx.stroke()
            self.lhatch = cairo.SurfacePattern(lhatch)

    def draw(self, ctx, page_w, page_h):

        """
        Draws a component. Mainly calls supporting functions.

        The drawing page class will call this function, which
        in turn calls draw_component(), which should be overridden
        by subclasses to provide drawing functionality for that
        specific component.

        Subclasses should not normally override draw() itself.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area

        Returns the scale factor of the drawn component, which is
        then used to show the scale on the page.
        """

        ctx.save()

        self.draw_pre_scale(ctx, page_w, page_h)

        self.set_scale(ctx, page_w, page_h)

        ctx.set_source_rgb(*self.drawing_line_color)
        ctx.set_line_width(self.drawing_line_width)

        self.draw_component(ctx, page_w, page_h)

        ctx.restore()

        return self.scale

    def draw_pre_scale(self, ctx, page_w, page_h):

        """
        Drawing actions to perform prior to scaling.

        Subclasses should override this if desired.
        """

        pass

    def set_scale(self, ctx, page_w, page_h):

        """
        Automatically sets a scale factor for the drawing.

        Subclasses should override this and call their
        parent class set_scale() function at the end of
        their own. 'page_h' and 'page_w' should already have been
        up-scaled by the time this happens and we get here.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- height and width of the drawing area
        """

        # Upscale dash style

        for dims in range(len(self.dash_style)):
            self.dash_style[dims] /= self.scale

        # Upscale fonts

        for key in self.text.iterkeys():
            self.text[key].size /= self.scale
            self.text[key].padding /= self.scale

        # Upscale lines

        self.drawing_line_width /= self.scale

    def draw_component(self, ctx, page_w, page_h):

        """
        Draws the drawn component.

        Subclasses should override this method and not call this.

        Arguments:
        ctx -- a Pycairo context
        page_w, page_h -- width and height of drawing area
        """

        ctx.save()

        notice = "Override this base class"
        draw_text_box(ctx=ctx, labels=[notice], textinfo=self.text["notice"],
                      centerpoint=Point(page_w / 2, page_h / 2), noborder=True)
        ctx.restore()
