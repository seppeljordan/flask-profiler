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
		    label: "Duration",
		    attribute: "elapsed",
		    formatting: "time",
		},
		{
		    label: "Time",
		    attribute: "startedAt",
		    formatting: "datetime",
		}
	    ]
	)
	controller.requestRemoteData()
    }

    document.addEventListener('DOMContentLoaded', (event) => {
        let button = document.getElementById("details-table-update-button");
        updateTarget(button);
        button.addEventListener("click", () => { updateTarget(button) });
    });
})()
