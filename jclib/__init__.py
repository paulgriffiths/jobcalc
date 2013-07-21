"""
Package for creating technical drawings of standard components.

The following page objects are imported:

  -- DrawingPage

along with the following job objects:

  -- PipeStraight
  -- PipeBend

To use, create a job object in the following format:

  -- PipeStraight(length, casingod, casingid,
                  liningod, liningid, flange)
  -- PipeBend(nomrad, casingod, casingid,
              liningod, liningid, bendangle,
              segangle, ctype, flange,
              exdimdrg, exdimbox)

and then a drawing page object in the following format:

  -- DrawingPage(component, otype="svg", osize="Letter",
                  title="", projno="", drgno="", qty="",
                  customer="", material="", bonding="",
                  finish="", servicetemp="", checkedby="")

where 'component' is the previously created job object.

Call:

  -- DrawingPage.draw(file)

to use.

The following helper functions are also imported:

  -- html_fail(msg)

"""

from jobcalc.pipestraight import PipeStraight
from jobcalc.pipebend import PipeBend
from jobcalc.page import DrawingPage
from jobcalc.helper import html_fail
