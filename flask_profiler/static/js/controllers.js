(function () {
    'use strict';
    var $controllers = {};
    self.$controllers = $controllers;

    $controllers.ShowSummaryController = class {
	constructor(
	    showSummaryPresenter,
	    httpClient,
	    requestTarget,
	    columnDefinitions,
	) {
	    this.showSummaryPresenter = showSummaryPresenter;
	    this.httpClient = httpClient;
	    this.requestTarget = requestTarget;
	    this.columnDefinitions = columnDefinitions;
	}
	requestRemoteData() {
	    let request = this.httpClient.request(this.requestTarget);
	    request.onResponse((response) => this.updateSummaryData(response));
	    request.send();
	}
	updateSummaryData(httpResponse) {
            if (httpResponse.status === 200) {
		let jsonResponse = JSON.parse(httpResponse.responseText);
		if (this.isResponseJsonValid(jsonResponse)) {
		    this.renderMeasurements(jsonResponse.measurements)
		}
	    }
	}
	isResponseJsonValid(responseJson) {
	    if (!(responseJson.measurements instanceof Array)) {
		return false
	    }
	    return true
	}
	renderMeasurements(measurements) {
	    this.showSummaryPresenter.updateElements(measurements, this.columnDefinitions)
	}
    }
})()
