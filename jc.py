#!/usr/bin/python

"""
JobCalc CGI Entry Point
=======================
Copyright 2013 Paul Griffiths
Email: mail@paulgriffiths.net

All rights reserved.

Also requires the following files on the web server:
 - jobcalc.html
 - jobcalc.css
 - jobcalc.js
"""

# Disable pylint refactor messages for too many
# statements, branches and local variables.
# pylint: disable=R0915
# pylint: disable=R0914
# pylint: disable=R0912


import cgi
import os
import sys
import jobcalc


def validate_form_option(form, field, name, allowed_values):

    """
    Gets a field from an HTML form, validates that it is present
    and is of an allowed value, and returns it.

    Arguments:
    form -- a form object returned from cgi.FieldStorage()
    field -- the name of the field in the HTML form
    name -- the name of the field to use for error messages
    allowed_values -- a Python list of allowed values for the field
    """

    value = form.getvalue(field)
    if value == None:
        jobcalc.html_fail("Type of {0} not specified!".format(name))
    if value not in allowed_values:
        jobcalc.html_fail("Invalid {0} type specified!".format(name))
    return value


def get_optional_form_field(form, field, default):

    """
    Gets an optional field from an HTML form, and returns its
    value if it's present, or a specified default if it's not.

    Arguments:
    form -- a form object returned from cgi.FieldStorage()
    field -- the name of the field in the HTML form
    default -- the default value to return if it's not present.
    """

    value = form.getvalue(field)
    return value if value else default


def main():

    """
    Main function for JobCalc CGI entry point.
    """

    form = cgi.FieldStorage()

    jobtypes = ["pipebend", "pipestraight"]
    pfields = ["casingod", "casingid", "liningod", "liningid"]
    sfields = ["length"]
    bfields = ["nomrad", "bendangle", "segangle"]
    ctypes = ["onepiece", "segmented"]
    flanges = ["100PN16", "125PN16", "150PN16", "200PN16",
                "250PN16", "300PN16", "400PN16"]
    otypes = ["pdf", "svg", "png"]
    osizes = ["A4", "Letter"]
    inputs = []

    # Determine job type

    jobtype = validate_form_option(form, "jobtype", "job", jobtypes)

    # Extend list of core job fields based on job type

    fields = pfields
    if jobtype == "pipebend":
        fields.extend(bfields)
    elif jobtype == "pipestraight":
        fields.extend(sfields)

    # Get and validate core job fields

    for field in fields:
        fstr = form.getvalue(field)

        if fstr == None:
            jobcalc.html_fail("Missing input &mdash; %s!" % field)

        try:
            if jobtype == "pipebend" and field == "segangle":
                num = float(fstr)
            else:
                num = int(fstr)
            inputs.append(num)

        except ValueError:
            jobcalc.html_fail("Bad value for %s!" % field)

    # Further validate core job fields

    for i, field in zip(inputs, fields):
        if not i > 0:
            jobcalc.html_fail("%s must be greater than zero!" % field)

    for i in range(0, 3):
        if not inputs[i] > inputs[i + 1]:
            jobcalc.html_fail("%s must be greater than %s!" %
                              (fields[i], fields[i + 1]))

    if jobtype == "pipebend":
        if not 0 < inputs[5] <= 90:
            jobcalc.html_fail("Bend angle must be greater than 0 " +
                              "degrees and no more than 90 degrees!")

        if round(inputs[5] * 100) % round(inputs[6] * 100):
            jobcalc.html_fail("Segment angle must divide into bend angle!")

    # Get and validate other required inputs

    if jobtype == "pipebend":
        casing = validate_form_option(form, "casing", "casing", ctypes)

        exdimdrg, exdimbox = False, False

        exdim = form.getlist("segdim")
        for opt in exdim:
            if opt == "drg":
                exdimdrg = True
            if opt == "box":
                exdimbox = True

    output = validate_form_option(form, "output", "output", otypes)
    flange = validate_form_option(form, "flange", "flange", flanges)
    osize = validate_form_option(form, "outputsize", "output size", osizes)

    qty = get_optional_form_field(form, "qty", "1")
    try:
        qty = int(qty)
    except ValueError:
        jobcalc.html_fail("Quantity needs to be an integer!")

    # Get optional inputs and provide defaults if necessary

    title = get_optional_form_field(form, "title", "")
    projno = get_optional_form_field(form, "projno", "")
    customer = get_optional_form_field(form, "customer", "")
    material = get_optional_form_field(form, "material", "")
    bonding = get_optional_form_field(form, "bonding", "")
    finish = get_optional_form_field(form, "finish", "")
    servicetemp = get_optional_form_field(form, "servicetemp", "")
    drgno = get_optional_form_field(form, "drgno", "")
    checkedby = get_optional_form_field(form, "checkedby", "")

    # Create job instance based on HTML form input
    # and draw the page for returning to the server.

    if jobtype == "pipebend":
        job = jobcalc.PipeBend(nomrad=inputs[4], casingod=inputs[0],
                  casingid=inputs[1], liningod=inputs[2],
                  liningid=inputs[3], bendangle=inputs[5],
                  segangle=inputs[6], ctype=casing,
                  exdimdrg=exdimdrg, exdimbox=exdimbox,
                  flange=flange)
    elif jobtype == "pipestraight":
        job = jobcalc.PipeStraight(casingod=inputs[0],
                  casingid=inputs[1], liningod=inputs[2],
                  liningid=inputs[3], length=inputs[4],
                  flange=flange)

    page = jobcalc.DrawingPage(otype=output, component=job, osize=osize,
                  title=title, projno=projno, drgno=drgno,
                  qty=qty, customer=customer, finish=finish,
                  servicetemp=servicetemp, bonding=bonding,
                  material=material, checkedby=checkedby)

    # Output HTTP header and draw page

    if output == "pdf":
        print("Content-type: application/pdf\n")
        outfile = sys.stdout
    elif output == "svg":
        print("Content-type: image/svg+xml\n")
        outfile = sys.stdout
    elif output == "png":
        outfile = os.fdopen(sys.stdout.fileno(), "wb")
        outfile.write("Content-type: image/png\r\n\r\n")

    page.draw(outfile)

    if output == "png":
        outfile.close()


# Call main() function if in __main__ namespace

if __name__ == "__main__":
    main()
