(function() {
    /*
      columnDefinition := {
        label: string,
        attribute: string,
        formatting: string,
      }
    */
    'use strict';
    var $datatable = {};
    self.$datatable = $datatable;

    $datatable.DatatableFilterInput = class extends HTMLInputElement {
	constructor() {
	    super();
	    this.addEventListener('input', (event) => this.updateTarget());
	}
	set targetId(value) {
	    this.setAttribute("target-id", value);
	}
	get targetId() {
	    return this.getAttribute("target-id");
	}
	updateTarget() {
	    let elementToUpdate = this.findElementToUpdate();
	    if (elementToUpdate) {
		this.updateElement(elementToUpdate);
	    }
	}
	findElementToUpdate() {
	    let elementId = this.targetId;
	    if (elementId) {
		return document.getElementById(elementId);
	    }
	}
	updateElement(element) {
	    element.setFilter(this.value);
	}
    }

    $datatable.SortableColumnHeader = class extends HTMLTableCellElement {
	constructor() {
	    super();
	    this.addEventListener('click', (event) => { this.updateSortingOrder() })
	    this.isAscending = false;
	}
	updateSortingOrder() {
	    let table = this.getContainingDataTable();
	    let columnName = this.sortColumnName;
	    if (table && columnName) {
		table.setSortingOrder(columnName, this.isAscending);
		this.isAscending = !this.isAscending;
	    }
	}
	getContainingDataTable() {
	    let targetId = this.targetId;
	    if (targetId) {
		return document.getElementById(targetId);
	    } else {
		return null
	    }
	    
	}
	set sortColumnName(value) {
	    this.setAttribute("sort-column-name", value);
	}
	get sortColumnName() {
	    return this.getAttribute("sort-column-name");
	}
	set targetId(value) {
	    this.setAttribute("target-id", value);
	}
	get targetId() {
	    return this.getAttribute("target-id");
	}
    }

    $datatable.DataTable  = class extends HTMLElement {
	constructor() {
	    super();
	    this.filterText = "";
	    this.isSortedAscendingly = true;
	    this.columnToSortAfter = null;
	}
	updateElements(dataItems, columnDefinitions) {
	    if (this.columnDefinitions !== columnDefinitions) {
		this.saveColumnDefinitions(columnDefinitions)
		this.clearDomChildren();
		this.drawTable();
	    }
	    this.dataItems = dataItems;
	    this.sortDataItems();
	    this.drawTableRows();
	}
	saveColumnDefinitions(definitions) {
	    this.columnDefinitions = [];
	    for (let column of definitions) {
		this.columnDefinitions.push({
		    label: column.label,
		    attribute: column.attribute,
		    formatting: $columns.selectColumnFormattingFromString(column.formatting),
		})
	    }
	}
	setFilter(filter) {
	    this.filterText = filter;
	    this.drawTableRows();
	}
	setSortingOrder(columnName, isAscending) {
	    this.isSortedAscendingly = isAscending;
	    this.columnToSortAfter = columnName;
	    this.sortDataItems();
	    this.drawTableRows();
	}
	sortDataItems() {
	    if (this.columnToSortAfter) {
		this.dataItems.sort((a,b) => this.compareDataItems(a,b))
	    }
	}
	drawTableRows() {
	    if (!this.dataItems) {
		return
	    }
	    let newChildren = new Array();
	    for (const element of this.dataItems) {
		if (
		    !this
			.concatenatedRowText(element)
			.includes(this.filterText)
		) {
		    continue
		}
		newChildren.push(this.createRow(element));
	    }
	    let body = this.querySelector('tbody');
	    if (!body) {
		return
	    }
	    while (body.firstChild) {
		body.removeChild(body.lastChild);
	    }
	    for (const child of newChildren) {
		body.append(child);
	    }
	}
	concatenatedRowText(dataRow) {
	    if (!this.columnDefinitions) {
		return ""
	    }
	    let completeText = "";
	    for (let column of this.columnDefinitions) {
		let columnValue = dataRow[column.attribute];
		let formattedValue = column.formatting(columnValue);
		completeText = completeText + " " + formattedValue;
	    }
	    return completeText
	}
	drawTable() {
	    let table = document.createElement("table");
	    let header = document.createElement("thead");
	    let body = document.createElement("tbody");
	    for (let columnDefinition of this.columnDefinitions) {
		header.append(
		    this.createHeader(
			columnDefinition.label,
			columnDefinition.attribute
		    )
		);
	    }
	    table.append(header);
	    table.append(body);
	    this.append(table)
	}
	createHeader(label, sortColumn) {
	    let cell = document.createElement("th", {
		is: "sortable-column-header",
	    })
	    cell.sortColumnName = sortColumn
	    cell.targetId = this.getAttribute("id")
	    cell.append(document.createTextNode(label));
	    return cell;
	}
	clearDomChildren() {
	    for (const element of this.children) {
		element.remove()
	    }
	}
	createRow(data) {
	    let element = document.createElement("tr");
	    for (let columnDefinition of this.columnDefinitions) {
		let columnValue = data[columnDefinition.attribute];
		let formattedValue = columnDefinition.formatting(columnValue);
		element.append(this.createColumn(formattedValue));
	    }
	    return element
	}
	createColumn(text) {
	    let element = document.createElement("td");
	    element.append(
		document.createTextNode(text)
	    )
	    return element
	}
	compareDataItems(a,b) {
	    let aValue = a[this.columnToSortAfter]
	    let bValue = b[this.columnToSortAfter]
	    let comparison;
	    if (aValue > bValue) {
		comparison = 1;
	    } else if (aValue < bValue) {
		comparison = -1;
	    } else {
		comparison = 0
	    };
	    if (!this.isSortedAscendingly) {
		comparison = -1 * comparison;
	    }
	    return comparison
	}
    }

    document.addEventListener('DOMContentLoaded', (event) => {
	for (let element of document.querySelectorAll("input")) {
	    if (element instanceof $datatable.DatatableFilterInput) {
		element.updateTarget()
	    }
	}
    });

    customElements.define("sortable-column-header", $datatable.SortableColumnHeader, {extends: "th"});
    customElements.define("data-table", $datatable.DataTable);
    customElements.define("datatable-filter-input", $datatable.DatatableFilterInput, {extends: "input"});
})()
