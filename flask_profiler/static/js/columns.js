(function() {
    'use strict';
    var $columns = {};
    self.$columns = $columns;

    $columns.formatTime = (x) => (x * 1000).toFixed(3) + " ms";
    $columns.formatString = (x) => x,
    $columns.formatNumber = (x) => x,
    $columns.formatDatetime = (x) => {
	let date = new Date(x * 1000);
	return date.toString();
    };
    $columns.selectColumnFormattingFromString = function (columnType) {
	return {
	    "string": $columns.formatString,
	    "time": $columns.formatTime,
	    "number": $columns.formatNumber,
	    "datetime": $columns.formatDatetime,
	}[columnType]
    }
})()
