
function create_navbar(user_signed_in, page) {
	/*
	Creates navigation bar object to be displayed on page

	Params:
		user_signed_in (bool): boolean of whether or not the user is signed in
		page (str): name of page or null
	*/

	// create navbar
	var navbar = d3.select("#navbar-container")
				   .append("nav")
				   .attr("class", "navbar navbar-expand-lg navbar-light bg-light");

	// create HKSToday brand text
	var brand =	navbar.append("a")
			  		  .attr("class", "navbar-brand")
			  		  .attr("href", "/#")
			  		  .html("<strong>HKS</strong>Today");
	
	// create toggle button for mobile views
	var toggle_button =	navbar.append("button")
							  .attr("class", "navbar-toggler")
							  .attr("type", "button")
							  .attr("data-toggle", "collapse")
							  .attr("data-target", "#navbarSupportedContent")
							  .attr("aria-controls", "navbarSupportedContent")
							  .attr("aria-expanded", "false")
							  .attr("aria-label", "Toggle navigation")

		toggle_button.append("span")
					 .attr("class", "navbar-toggler-icon");

	// create collapsible bar to hold buttons
	var collapsible_bar = navbar.append("div")
								.attr("class", "collapse navbar-collapse")
								.attr("id", "navbarSupportedContent");

	var button_list = collapsible_bar.append("ul")
									 .attr("class", "navbar-nav mr-auto");

	// if user signed in, add preferences, add event, and log out buttons
	if (user_signed_in) {
		
		// don't display preferences button on preferences page
		if (page !== 'preferences') {
			button_list.append("li")
					   .attr("class", "nav-item")
					   .append("a")
				   		   .attr("class", "nav-link")
				   		   .attr("href", "/preferences")
				   		   .html("Preferences");
		}

		// don't display add event button on add event page
		if (page !== 'add_event') {
			button_list.append("li")
					   .attr("class", "nav-item")
					   .append("a")
				   		   .attr("class", "nav-link")
				   		   .attr("href", "/add_event")
				   		   .html("Add Event");
		}

		button_list.append("li")
				   .attr("class", "nav-item")
				   .append("a")
			   		   .attr("class", "nav-link")
			   		   .attr("href", "/logout")
			   		   .html("Log Out");

	// if user not signed in add sign in by google button
	} else {
		button_list.append("li")
				   .attr("class", "nav-item")
				   .append("button")
			   		   .attr("class", "login-button btn btn-outline-success my-2 my-sm-0")
					   .attr("onclick", "location.href='/login'");
	}

	// add search form
	var search_form	= collapsible_bar.append("form")
									 .attr("action", "/#")
									 .attr("method", "get")
									 .attr("class", "form-inline my-2 my-lg-0");

		search_form.append("input")
				   .attr("type", "search")
				   .attr("class", "form-control mr-sm-2")
				   .attr("placeholder", "Search...")
				   .attr("aria-label", "Search")
				   .attr("name", "search");

		search_form.append("button")
				   .attr("class", "btn btn-outline-success my-2 my-sm-0")
				   .attr("type", "submit")
				   .html("Search");
}