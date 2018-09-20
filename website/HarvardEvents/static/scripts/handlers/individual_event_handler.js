function display_individual_event_page(current_user_authentication, data) {
	user_signed_in = (current_user_authentication == 'True');
	create_navbar(user_signed_in, null);
	show_individual_event(data);
	$("[data-toggle=tooltip").tooltip();
}

function show_individual_event(data) {
	var individual_event_container = d3.select("#individual-event-container");
	var info_main_container = individual_event_container.append("div")
														.attr("class", "col-sm-8 info-main");
		info_main_container.append("div")
						   .attr("class", "event-page-title")
						   .html(data["title"]);

		info_main_container.append("p")
						   .attr("class", "event-page-subtitle")
						   .html(data["date"] + " from " + data["timing"] + " in " + data["location"]);

		info_main_container.append("div")
						   .attr("class", "event-full-description")
						   .html(data["description"]);

	var info_sidebar_container = individual_event_container.append("div")
														   .attr("class", "col-sm-3 col-sm-offset-1");

	var info_sidebar_module = info_sidebar_container.append("div")
													.attr("class", "info-sidebar")

	if (data["rsvp_date"]) {
		info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("RSVP Date");

		info_sidebar_module.append("p")
							  .attr("class", "contact-info-value")
							  .html(data["rsvp_date"]);
	}

	if (data["rsvp_required"] != 'No') {
		if (data["rsvp_required"].includes("@")) {
			info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("RSVP Email");

			info_sidebar_module.append("p")
								  .attr("class", "contact-info-value")
								  .append("a")
								  		.attr("href",  "mailto:" + data["rsvp_required"])
								  		.html(data["rsvp_required"]);
		} else if (data["rsvp_required"].includes(".")) {
			info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("RSVP URL");

			info_sidebar_module.append("p")
								  .attr("class", "contact-info-value")
								  .append("a")
								  		.attr("href",  data["rsvp_required"])
								  		.html(data["rsvp_required"]);
		} else {
			info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("RSVP Required");

			info_sidebar_module.append("p")
								  .attr("class", "contact-info-value")
								  .html(data["rsvp_required"]);
		}

	}

	if (data["ticketed_event_instructions"]) {
		info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("Ticketed Event?");

		info_sidebar_module.append("p")
							  .attr("class", "contact-info-value")
							  .html("Yes");

		info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("Ticket Instructions");

		info_sidebar_module.append("p")
							  .attr("class", "contact-info-value")
							  .html(data["ticketed_event_instructions"]);
	}

	if (data["contact_name"]) {
		info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("Contact Name");

		info_sidebar_module.append("p")
							  .attr("class", "contact-info-value")
							  .html(data["contact_name"]);
	}

	if (data["contact_email"]) {
		info_sidebar_module.append("h5")
							  .attr("class", "contact-info-label")
							  .html("Contact Email");

		info_sidebar_module.append("p")
							  .attr("class", "contact-info-value")
							  .append("a")
							  		.attr("href", "mailto:" + data["contact_email"])
							  		.html(data["contact_email"]);
	}

	info_sidebar_container.append("button")
						  .attr("class", "google-cal-big")
						  .attr("onclick", "location.href='/add_to_google_cal/" + data["event_id"] + "/site;'")
						  .attr("data-toggle", "tooltip")
						  .attr("data-placement", "top")
						  .attr("title", "Add to Google Calendar");

}