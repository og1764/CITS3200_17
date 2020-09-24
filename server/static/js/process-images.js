function processFiles() {
    $.get("/result", function(data, status){
		document.getElementById("p1").innerHTML = data;
		document.getElementById("p2").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
	});
  }