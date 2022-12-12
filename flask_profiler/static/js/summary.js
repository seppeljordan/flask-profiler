(function() {
    function updateTarget(button) {
	let controller = new $controllers.ShowSummaryController(
	    document.getElementById(button.getAttribute("target-id")),
	    new $httpClient.HttpClient(),
	    button.getAttribute("endpoint"),
	    [
		{
		    label: "Method",
		    attribute: "method",
		    formatting: "string",
		},
		{
		    label: "Name",
		    attribute: "name",
		    formatting: "string",
		},
		{
		    label: "#Requests",
		    attribute: "count",
		    formatting: "number",
		},
		{
		    label: "Avg. response time",
		    attribute: "avgElapsed",
		    formatting: "time",
		},
		{
		    label: "Min. response time",
		    attribute: "minElapsed",
		    formatting: "time",
		},
		{
		    label: "Max. response time",
		    attribute: "maxElapsed",
		    formatting: "time",
		},
	    ]
	)
	controller.requestRemoteData()
    }

    document.addEventListener('DOMContentLoaded', (event) => {
        let button = document.getElementById("summary-table-update-button");
        updateTarget(button);
        button.addEventListener("click", () => { updateTarget(button) });
    });
})()
