
function display_user_preferences_page(current_user_authentication, data) {
	user_signed_in = (current_user_authentication == 'True');
	create_navbar(user_signed_in, 'preferences');
	show_preferences(data);
	$("[data-toggle=tooltip").tooltip();
	setTimeout(function () { $(".alert").hide() }, 2000);
}

function show_preferences(data) {
	var preferences_container = d3.select("#preferences-container");

	var email_form = create_preferences_row(preferences_container, "Email", "email", "email");
		email_form.attr("class", "form-inline my-2 my-lg-0");
	var email_form_input_group = email_form.append("div")
				  						   .attr("class", "input-group");
		
		email_form_input_group.append("input")
							  .attr("type", "email")
							  .attr("class", "form-control")
							  .attr("name", "email")
							  .attr("placeholder", data["email"])
							  .property("required", true);

		email_form_input_group.append("button")
							  .attr("class", "btn btn-outline-warning my-2 my-sm-0")
							  .attr("type", "submit")
				   			  .html("Change");

	var weekly_events_email_form = create_preferences_row(preferences_container, "Weekly Events Email", "daily_subscription", data["daily_subscribed"]);
	create_preferences_switch(weekly_events_email_form, data["daily_subscribed"]);

	var new_events_email_form = create_preferences_row(preferences_container, "New Events Email", "newevents_subscription", data["newevents_subscribed"]);
	create_preferences_switch(new_events_email_form, data["newevents_subscribed"]);

	var recommended_events_email_form = create_preferences_row(preferences_container, "Recommended Events Email", "recommendation_subscription", data["recommendation_subscribed"]);
	create_preferences_switch(recommended_events_email_form, data["recommendation_subscribed"]);

	create_events_row(preferences_container, 'Submitted', data['submitted_events']);
	create_events_row(preferences_container, 'Upcoming', data['upcoming_events']);
	create_events_row(preferences_container, 'Previous', data['previous_events']);
}

function create_preferences_row(container, title, param_name, param_value) {
	var row_container = container.append("div")
								 .attr("class", "row prefereces-row");

		row_container.append("div")
					 .attr("class", "preferences-group-header mr-auto")
					 .html(title);

	var action_url = (title == 'Email') ? "/change_preferences" : "/change_preferences?" + param_name + "=" + param_value;
	var row_form = row_container.append("form")
					 			.attr("action", action_url)
					 			.attr("method", "post");

	return row_form
}

function create_preferences_switch(form, param_value) {
	var label = form.append("label")
					.attr("class", "switch");

		label.append("input")
			 .attr("type", "checkbox")
			 .property('checked', param_value)
			 .attr("onchange", "this.form.submit()");

		label.append("span")
			 .attr("class", "slider round")
			 .attr("data-toggle", "tooltip")
			 .attr("data-placement", "top")
			 .attr("title", (param_value) ? "Subscribed" : "Not Subscribed");
}

function create_events_row(container, title, event_list) {
	var events_row = container.append("div")
							  .attr("class", "row prefereces-row");

		events_row.append("div")
			      .attr("class", "preferences-group-header-event")
			      .html(title + " Events");

	if (event_list.length > 0) {
		for (event_index in event_list) {
			var event = event_list[event_index];
			var event_link = "/" + event["id"] + "/site";
			if (title == 'Submitted') {
				var event_row = events_row.append("div")
				  		  			  	  .attr("class", "submitted-events-row");

				  	event_row.append("a")
						  	 .attr("href", event_link)
						  	 .attr("class", "preferences-event")
						  	 .html(event["title"]);

					if (event["upcoming_flag"]) {
						event_row.append("button")
								 .attr("class", "btn btn-warning edit-button")
								 .attr("onclick", "location.href='/add_event?edit=" + event["id"] + "'")
								 .html("Edit");
					}

			} else {
				events_row.append("a")
						  .attr("href", event_link)
						  .attr("class", "preferences-event")
						  .html(event["title"]);
			}
			
		}
		
	} else {
		events_row.append("p")
				  .attr("class", "event-page-subtitle")
				  .html("No " + title + " Events");
	}
}