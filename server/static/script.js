function processFiles() {
	//Dropzone.forElement('.dropzone').processQueue();
    $.get("/result", function(data, status){
		document.getElementById("output").innerHTML = data;
		document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
	});
}

function copyToClipboard(element) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val($(element).text()).select();
    document.execCommand("copy");
    $temp.remove();
}
