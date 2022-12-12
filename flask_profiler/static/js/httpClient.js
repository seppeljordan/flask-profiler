(function () {
    'use strict';
    var $httpClient = {};
    self.$httpClient = $httpClient;

    $httpClient.Request = class {
	constructor(xmlHttpRequest) {
	    this.request = xmlHttpRequest
	}
	onResponse(callback) {
	    this.request.onreadystatechange = () => {
		if (this.request.readyState === XMLHttpRequest.DONE) {
		    callback(this.request);
		}
	    };
	}
	send() {
	    this.request.send();
	}
    }
    $httpClient.HttpClient = class {
	request(requestTarget) {
	    let httpRequest = new XMLHttpRequest();
	    httpRequest.open("GET", requestTarget);
	    return new $httpClient.Request(httpRequest);
	}
    }
})()

