
function display_add_event_page(current_user_authentication, data) {
	user_signed_in = (current_user_authentication == 'True');
	create_navbar(user_signed_in, 'add_event');
	show_add_event(data)
}

function show_add_event(data) {
	var container = d3.select("#add-event-container");
	var form_url = (data['event_data']['type'] == 'edit') ? '/add_event?edit=' + data['event_data']['info']['id'] : '/add_event';
	var form = container.append("form")
					    .attr("method", "post")
					    .attr("action", form_url);

	create_form_group(form, "Title", "text", "title", "input", data["event_data"], true, null);
	create_form_group(form, "Date", "date", "date", "input", data["event_data"], true, data["min_date"]);
	create_form_group(form, "Start Time", "time", "start_time", "input", data["event_data"], true, null);
	create_form_group(form, "End Time", "time", "end_time", "input", data["event_data"], true, null);
	create_form_group(form, "Location", "text", "location", "input", data["event_data"], true, null);
	create_form_group(form, "Description", "text", "description", "textarea", data["event_data"], false, null);
	create_form_group(form, "RSVP Deadline <i>(leave blank if no RSVP required)</i>", "date", "rsvp_deadline", "input", data["event_data"], false, data["min_date"]);
	create_form_group(form, "RSVP Email or URL <i>(leave blank if no RSVP required, make sure to include http://)</i>", "text", "rsvp_email_url", "input", data["event_data"], false, null);
	create_form_group(form, "Ticketed Event Instructions <i>(leave blank if no ticket required)</i>", "text", "ticketed_event_instructions", "textarea", data["event_data"], false, null);
	create_form_group(form, "Contact Name", "text", "contact_name", "input", data["event_data"], false, null);
	create_form_group(form, "Contact Email", "email", "contact_email", "input", data["event_data"], false, null);

	form.append("button")
		.attr("type", "submit")
		.attr("class", "btn btn-outline-success event-submit")
		.html("Submit");

	if (data['event_data']['type'] == 'edit') {
		container.append("form")
				 .attr("action", '/delete_event/' + data['event_data']['info']['id'])
				 .attr("method", "post")
				 .attr("onsubmit", "return confirm('Are you sure you want to delete?');")
				 .append("button")
				 	.attr("class", "btn btn-outline-danger")
				 	.html("Delete");
	}
}

function create_form_group(form, label, type, name, input_type, event_data, required, min) {
	form.append("label")
		.html(label);

	var form_input = form.append(input_type)
						 .attr("class", "form-control")
						 .attr("type", type)
						 .attr("name", name)
						 .property("required", required);

		if (event_data["type"] == 'edit') {
			form_input.attr("value", event_data["info"][name]);
		}

		if (min !== null) {
			form_input.attr("min", min);
		}

}