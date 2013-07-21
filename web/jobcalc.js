//  jobcalc.js
//  ==========
//  Copyright 2013 Paul Griffiths
//  Email: mail@paulgriffiths.net
//
//  Functions for JobCalc CGI interface

function changejob(form) {
	var ba = ["bendattr_r", "nomrad_r", "bendangle_r", "segangle_r", "casingtype_r", "segdim_r", "segdim2_r"];
	var sa = ["straightattr_r", "length_r"];

	if ( form.jobtype.selectedIndex == 0 ) {
		for ( var i=0; i < ba.length; ++i ) {
			document.getElementById(ba[i]).style.display = "table-row";	
		}
		for ( var i=0; i < sa.length; ++i ) {
			document.getElementById(sa[i]).style.display = "none";	
		}
	}
	else if ( form.jobtype.selectedIndex == 1 ) {
		for ( var i=0; i < ba.length; ++i ) {
			document.getElementById(ba[i]).style.display = "none";	
		}
		for ( var i=0; i < sa.length; ++i ) {
			document.getElementById(sa[i]).style.display = "table-row";	
		}
	}
}


