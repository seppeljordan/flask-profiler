class DependencyInjector {
    getShowSummaryController() {
	if (!this.showSummaryController) {
	    this.showSummaryController = new $controllers.ShowSummaryController(
		this.getPresenter(),
		this.getHttpClient(),
		"fake request target",
		"fake column definitions",
	    );
	}
	return this.showSummaryController
    }
    getHttpClient() {
	if (!this.httpClient) {
	    this.httpClient = new FakeHttpClient();
	}
	return this.httpClient;
    }
    getPresenter() {
	if (!this.presenter) {
	    this.presenter = new FakePresenter();
	}
	return this.presenter;
    }
}


class FakePresenter {
    constructor() {
	this.renderedElements = null;
	this.renderedColumnDefinitiosn = null;
    }
    updateElements(elements, columnDefinitions) {
	this.renderedElements = elements;
	this.renderedColumnDefinitions = columnDefinitions;
    }
}

class FakeRequest {
    constructor(status, responseText) {
	this.status = status
	this.responseText = responseText
    }
    onResponse(callback) {
	this.callback = callback
    }
    send() {
	if (this.callback) {
	    this.callback({
		status: this.status,
		responseText: this.responseText,
	    })
	}
    }
}

class FakeHttpClient {
    constructor() {
	this.status = 200
	this.responseText = JSON.stringify({
	    status: 200,
	    measurements: [],
	});
    }
    request(target) {
	return new FakeRequest(this.status, this.responseText);
	
    }
    prepareFollowingResponses({measurements = [], status = 200} = {}) {
	this.status = status;
	this.repsonseText = JSON.stringify({
	    measurements: measurements
	});
    }
}

function makeResponse({measurements = [], status = 200} = {}) {
    responseJson = JSON.stringify({
	measurements: measurements
    });
    return {
	status: status,
	responseText: responseJson
    }
}

function test(description, testFunction, testInputs = null) {
    if (testInputs) {
	for (let inputData of testInputs) {
	    try {
		testFunction(inputData);
		console.log('\u2714 ' + description + ' (' + inputData + ')');
	    } catch (error) {
		console.log('\n');
		console.log('\u2718 ' + description + ' (' + inputData + ')');
		console.error(error);
		console.log('\n');	
	    }
	}
    } else {
	try {
	    testFunction();
	    console.log('\u2714 ' + description);
	} catch (error) {
	    console.log('\n');
	    console.log('\u2718 ' + description);
	    console.error(error);
	    console.log('\n');	
	}
    }
}

function assert(condition) {
    if (!condition) {
      throw new Error();
    }
}

test("ShowSummaryController renders empty list when handling response with empty measurements", () => {
    let injector = new DependencyInjector()
    let presenter = injector.getPresenter();
    let controller = injector.getShowSummaryController();
    controller.updateSummaryData(makeResponse({measurements: []}));
    assert(presenter.renderedElements instanceof Array);
    assert(!presenter.renderedElements.length);
})

test(
    "ShowSummaryController renderes nothing when response status is not 200",
    (statusCode) => {
	let injector = new DependencyInjector()
	let presenter = injector.getPresenter();
	let controller = injector.getShowSummaryController();
	controller.updateSummaryData(makeResponse({status: 400}));
	assert(presenter.renderedElements === null)
    },
    testInputs = [400, 500, 302],
)

test(
    "ShowSummaryController renders nothing when measurements in response are not an array",
    (measurement) => {
	let injector = new DependencyInjector()
	let presenter = injector.getPresenter();
	let controller = injector.getShowSummaryController();
	controller.updateSummaryData(makeResponse({measurements: measurement}));
	assert(presenter.renderedElements === null)
    },
    testInputs = [null, {}, 1, "1", true, false],
)

test(
    "ShowSummaryController eventually renders something when update is requested and response is success",
    () => {
	let injector = new DependencyInjector()
	let httpClient = injector.getHttpClient();
	let presenter = injector.getPresenter();
	let controller = injector.getShowSummaryController();
	httpClient.prepareFollowingResponses({measurements: []});
	controller.requestRemoteData();
	assert(presenter.renderedElements instanceof Array);
    }
)
