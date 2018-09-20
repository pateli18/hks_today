
function display_index_page(current_user_authentication, data_raw, scroll) {
	user_signed_in = (current_user_authentication == 'True');
	create_navbar(user_signed_in, null);
	process_event_data(data_raw);
	$("[data-toggle=tooltip").tooltip();
	setTimeout(function () { $("#success-alert").hide()}, 2000);
	if (scroll != 'None') {
		document.getElementById(scroll).scrollIntoView();
	}
}


function process_event_data(data_raw) {
	var nested_events = d3.nest()
						  .key(function(d) { return d.date; })
						  .entries(data_raw['all_events']);

	data_raw["all_events"] = nested_events;
	show_events(data_raw);
}


function show_events(data) {
	var primary_container = d3.select("#events-container");
	if (data['search_term']) {
		primary_container.append("div")
						 .attr("class", "row search-results")
						 .html(data['num_search_events'] + " events found with " + data['search_term'] + "...");
	}
	for (item_index in data['all_events']) {
		var item = data["all_events"][item_index];
		var row = primary_container.append("div")
								   .attr("class", "row");

			row.append("div")
				.attr("class", "event-group-header")
				.html(item.key);

		for (event_index in item.values) {
			var event = item.values[event_index];
			var event_card = row.append("div")
								.attr("id", "event_" + event["event_id"])
								.attr("class", "card event");

			var title_container = event_card.append("div")
											.attr("class", "event-title-container");

				title_container.append("a")
							   .attr("href", "/" + event["event_id"] + "/site")
							   .append("div")
							   		.attr("class", "event-title")
							   		.html(event["title"]);

				title_container.append("button")
							   .attr("class", "google-cal")
							   .attr("onclick", "location.href='/add_to_google_cal/" + event["event_id"] + "/site';")
							   .attr("data-toggle", "tooltip")
							   .attr("data-placement", "top")
							   .attr("title", ((event['user_flag']) ? 'Already added to Calendar!' : 'Add to Google Calendar'));

				if (event['user_flag']) {
					title_container.append("div")
								   .attr("class", "event-selected-flag");
				}

			var event_info_table = event_card.append("table")
											 .attr("class", "event-info");

			var first_trow = event_info_table.append("tr");
				first_trow.append("td")
						  .attr("class", "event-info-label")
						  .html("Time");
				first_trow.append("td")
						  .html(event["timing"]);

			var second_trow = event_info_table.append("tr");
				second_trow.append("td")
						   .attr("class", "event-info-label")
						   .html("Location");
				second_trow.append("td")
						   .html(event["location"]);

			var third_trow = event_info_table.append("tr");
				third_trow.append("td")
						  .attr("class", "event-info-label")
						  .html("RSVP");

				if (event["rsvp_required"] != 'No') {
					if (event["rsvp_required"].includes("@")) {
						third_trow.append("td")
								  .append("a")
								  .attr("href", "mailto:" + event["rsvp_required"])
								  .html(event["rsvp_required"]);

					} else if (event["rsvp_required"].includes(".")) {
						third_trow.append("td")
								  .append("a")
								  .attr("href", event["rsvp_required"])
								  .html(event["rsvp_required"]);
					} else {
						third_trow.append("td")
								  .html(event["rsvp_required"]);
					}
				} else {

					third_trow.append("td")
						  .html(event["rsvp_required"]);
				}
				
				event_card.append("p")
						  .attr("class", "event-description")
						  .html(event["description"]);
		}
	}
}