"""
Provides a class to construct a technical drawing page.
"""

# Copyright 2013 Paul Griffiths
# Email: mail@paulgriffiths.net
#
# Version 1.0.1, unreleased

# Disable pylint messages for:
#  - too short variable names, used extensively in this module
#  - too many arguments, possible future refactor
#  - too many local variables, possible future refactor
#  - too many instance attributes, possible future refactor
#
# pylint: disable=C0103
# pylint: disable=R0914
# pylint: disable=R0913
# pylint: disable=R0902


import cairo
import tempfile
import datetime
from jobcalc.helper import Point, LabeledValue, TextInfo, draw_text_box


class DrawingPage:

    """
    Drawing page class, provides a page to frame the drawn component.
    """

    def __init__(self, component, otype="svg", osize="Letter", title="",
                 projno="", drgno="", qty="", customer="", material="",
                 bonding="", finish="", servicetemp="", checkedby=""):

        """
        Initializes a DrawingPage instance.

        Arguments:
        component -- the component to draw
        otype -- format of desired output, "pdf", or "svg".
        osize -- desired output size, "A4" or "Letter"
        title, projno, drgno, qty, customer, material, bonding,
        finish, servicetemp, checkby -- miscellaneous information
        """

        # Page dimensions and properties

        self.client = "Clientname Limited"
        self.page_margin = 50
        self.page_inner_margin = 10
        self.page_inner_margin_x = 0
        self.page_inner_margin_y = 0
        self.page_infoboxheight = 100
        self.page_infoboxspacing = 5
        self.page_line_width = 0.5
        self.line_color = (0, 0, 0)
        self.scale_p = Point(0, 0)
        self.output_type = otype
        self.component = component

        self.text = {"info": TextInfo(face="Arial", size=8,
                                      padding=3, color=(0, 0, 0)),
                     "copyright": TextInfo(face="Arial", size=8,
                                           padding=3, color=(0.757, 0, 0.702)),
                     "title": TextInfo(face="Arial", size=10,
                                       padding=3, color=(0.0, 0.0, 0.4)),
                     "client": TextInfo(face="Arial", bold=True, size=12,
                                       padding=3, color=(0.757, 0, 0.702)),
                     "notice": TextInfo(face="Arial", size=10,
                                       padding=3, color=(0.0, 0.0, 0.0))}

        # Set page dimensions in points

        if osize == "A4":
            self.page_width = 596
            self.page_height = 843
        elif osize == "Letter":
            self.page_width = 612
            self.page_height = 792

        # Drawing information

        now = datetime.datetime.now()
        date_label = "%d/%d/%d" % (now.day, now.month, now.year)

        self.drg_info = {"title": LabeledValue("Title", title),
                         "cust": LabeledValue("Customer", customer),
                         "projno": LabeledValue("Proj. No.", projno),
                         "drgno": LabeledValue("DRG No.", drgno),
                         "qty": LabeledValue("Qty", "%d off" % (qty)),
                         "mat": LabeledValue("Material", material),
                         "bond": LabeledValue("Bonding sys.", bonding),
                         "finish": LabeledValue("Finish", finish),
                         "svctemp": LabeledValue("Svc. temp.", servicetemp),
                         "date": LabeledValue("Date", date_label),
                         "scale": LabeledValue("Scale", ""),
                         "drwnby": LabeledValue("Drawn by", "JobCalc v1.0"),
                         "chkby": LabeledValue("Checked by", checkedby)}

    def draw(self, outfile):

        """
        Master function for creating the drawing.

        This is the only public drawing function.
        """

        if self.output_type == "pdf":
            surface = cairo.PDFSurface(outfile,
                                       self.page_width, self.page_height)
        elif self.output_type == "svg":
            surface = cairo.SVGSurface(outfile,
                                       self.page_width, self.page_height)
        elif self.output_type == "png":
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                       self.page_width, self.page_height)

        self.ctx = cairo.Context(surface)

        if self.output_type == "png":
            self.ctx.save()
            self.ctx.set_source_rgb(1.0, 1.0, 1.0)
            self.ctx.paint()
            self.ctx.restore()

        self.draw_base_page()
        self.draw_drawing_info()
        self.draw_component()

        if self.output_type == "pdf" or self.output_type == "svg":
            surface.show_page()
        elif self.output_type == "png":
            imgfile = tempfile.TemporaryFile()
            surface.write_to_png(imgfile)
            imgfile.seek(0)
            outfile.write(imgfile.read())
            imgfile.close()

    def draw_base_page(self):

        """
        Draws the base page.
        """

        pw = self.page_width - self.page_margin * 2
        ph = self.page_height - self.page_margin * 2

        self.ctx.save()
        self.ctx.translate(self.page_margin, self.page_margin)
        self.ctx.set_line_width(self.page_line_width)
        self.ctx.set_source_rgb(*self.line_color)

        # Draw main margins

        self.ctx.rectangle(0, 0, pw, ph)
        self.ctx.stroke()

        # Draw dimension information and bounding box

        # pylint: disable=W0612

        (bw, bh, fps) = draw_text_box(ctx=self.ctx, topright=Point(pw, 0),
                                labels=["ALL DIMENSIONS ARE IN mm"],
                                textinfo=self.text["notice"], noborder=True)

        # pylint: enable=W0612

        self.ctx.move_to(pw - bw, 0)
        self.ctx.line_to(pw - bw, bh)
        self.ctx.line_to(pw, bh)
        self.ctx.stroke()

        self.page_inner_margin_y += bh

        self.ctx.restore()

    def draw_drawing_info(self):

        """
        Draws the information boxes.
        """

        pw = self.page_width - self.page_margin * 2
        ph = self.page_height - self.page_margin * 2
        ibs = self.page_infoboxspacing

        self.ctx.save()
        self.ctx.translate(self.page_margin, self.page_margin)
        self.ctx.set_line_width(self.page_line_width)
        self.ctx.set_source_rgb(*self.line_color)

        # Calculate info box widths

        self.ctx.select_font_face(*self.text["client"].face)
        self.ctx.set_font_size(self.text["client"].size)

        # pylint: disable=W0612

        (bx, by, w, h, dx, dy) = self.ctx.text_extents(self.client)

        # pylint: enable=W0612

        cbw = w + self.text["client"].padding * 2
        ibw = (pw - cbw - ibs * 5) / 3

        # Draw main info boxes

        x = ibs
        y = ph - ibs
        keys = [["cust", "projno", "drgno", "qty"],
                ["mat", "bond", "finish", "svctemp"],
                ["date", "scale", "drwnby", "chkby"]]

        for k in keys:
            labels, fields = zip(*[(self.drg_info[j].label,
                                    self.drg_info[j].value) for j in k])

            # pylint: disable=W0612

            (bw, bh, fps) = draw_text_box(ctx=self.ctx, bottomleft=Point(x, y),
                                  labels=labels, fields=fields,
                                  textinfo=self.text["info"], width=ibw)

            # pylint: enable=W0612

            if k[1] == "scale":
                self.scale_p = fps[1]

            x += (ibw + ibs)

        # Draw copyright box

        x = ibs
        y -= ibs + bh
        width = ibw * 3 + ibs * 2
        (bw, bh, fps) = draw_text_box(ctx=self.ctx, bottomleft=Point(x, y),
                              width=width,
                              labels=["Industrial copyright " + self.client],
                              textinfo=self.text["copyright"], center=True)

        # Draw title box

        y -= ibs + bh
        (bw, bh, fps) = draw_text_box(ctx=self.ctx, bottomleft=Point(x, y),
                               width=width,
                               labels=[self.drg_info["title"].value],
                               textinfo=self.text["title"], center=True)

        # Set info box height

        self.page_infoboxheight = ph - (y - ibs - bh)
        ibh = self.page_infoboxheight

        # Draw Omegaslate box

        self.ctx.select_font_face(*self.text["client"].face)
        self.ctx.set_font_size(self.text["client"].size)

        (bx, by, w, h, dx, dy) = self.ctx.text_extents(self.client)

        x = pw - ibs - w - self.text["client"].padding
        y = ph - ibh + ibs + self.text["client"].padding + h
        self.ctx.move_to(x, y)
        self.ctx.set_source_rgb(*self.text["client"].color)
        self.ctx.show_text(self.client)
        self.ctx.set_source_rgb(*self.line_color)

        self.ctx.rectangle(x - self.text["client"].padding,
                      y - h - self.text["client"].padding, cbw, ibh - ibs * 2)
        self.ctx.stroke()

        olabs = ["Address 1",
                 "Address 2",
                 "Company Tag Line",
                 "Telephone and Fax"]

        self.ctx.select_font_face(*self.text["info"].face)
        self.ctx.set_font_size(self.text["info"].size)
        self.ctx.set_source_rgb(*self.text["info"].color)

        for row, lstr in zip(range(len(olabs)), olabs):
            if row == 2 or row == 3:
                mult = 2.5
            else:
                mult = 1

            y += (h + self.text["client"].padding) * mult
            (bx, by, w, h, dx, dy) = self.ctx.text_extents(lstr)
            x = pw - ibs - (cbw / 2) - (w / 2)
            self.ctx.move_to(x, y)
            self.ctx.show_text(lstr)

        # Draw infobox divider

        self.ctx.set_source_rgb(*self.line_color)
        self.ctx.move_to(0, ph - ibh)
        self.ctx.line_to(pw, ph - ibh)
        self.ctx.stroke()

        self.ctx.restore()

    def draw_component(self):

        """
        Sets the drawing area and calls the component's draw method.
        """

        m = self.page_margin + self.page_inner_margin
        x = m + self.page_inner_margin_x
        y = m + self.page_inner_margin_y
        w = self.page_width - m * 2
        h = self.page_height - self.page_infoboxheight - y * 2

        self.ctx.save()
        self.ctx.translate(x, y)
        p_scale = self.component.draw(self.ctx, w, h)
        self.ctx.restore()

        # Format and show drawing scale
        #
        # Each pixel in device space is one point, of which there are
        # 72 in an inch. Nominal measurements are in millimeters, so
        # to get the scale convert millimeters to points -- 1mm is
        # 72/25.4 points -- and multiply by 100 to avoid showing a
        # ratio containing decimals.

        p_scale = (7200.0 / 25.4) / p_scale
        self.drg_info["scale"].value = "100:%d" % (round(p_scale))

        self.ctx.save()
        self.ctx.set_line_width(self.page_line_width)
        self.ctx.set_source_rgb(*self.line_color)
        self.ctx.select_font_face(*self.text["info"].face)
        self.ctx.set_font_size(self.text["info"].size)
        self.ctx.move_to(*self.scale_p.t())
        self.ctx.show_text(self.drg_info["scale"].value)
        self.ctx.restore()
