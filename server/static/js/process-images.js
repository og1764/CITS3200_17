function processFiles() {
    $.get("/result", function(data, status){
		document.getElementById("p1").innerHTML = data;
	});
  }