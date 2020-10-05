function copyToClipboard(element) {
  var $temp = $("<textarea>");
  var brRegex = /<br\s*[\/]?>/gi;
  $("body").append($temp);
  $temp.val($(element).html().replace(brRegex, "\r\n")).select();
  document.execCommand("copy");
  $temp.remove();
}

function Get_Function(url, thi, token) {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("output").innerHTML = xhttp.responseText;
			//document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
			if (status == "Example text"){
				document.getElementById("results").innerHTML = "";
			} else {
				// might have to change this to calling a function if it still doesnt like the URL
				document.getElementById("results").innerHTML = '<a href="/getResults/'.concat(status,'" download><button>Download</button></a>');
			}
			thi.removeAllFiles()
		}
	};
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
	xhttp.send();
}	

Dropzone.autoDiscover = false;
	
var myDropzone = new Dropzone(".dropzone", {
  //addRemoveLinks: true,
  autoProcessQueue: false,
  addRemoveLinks: true,
  maxFiles: 10,
  parallelUploads: 10,
  uploadMultiple: true,
  url: "/upload",
  init: function() {
	this.on("successmultiple", function(data, status) {
		document.getElementById("output").innerHTML = "Loading...";
		Get_Function('/start', this, status);
	});
  },
});

// Un-used, but potentially usable functions kept below just in case.

function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}


// This was part of an attempt at a progress bar
function Get_Progress(values) {
	if (values[1] != values[2]){
		console.log(values);
		move(values[1], values[2])
		sleep(3000);
		loadDoc('/progress/'.concat(values[3]), Get_Progress);
	} else {
		move(values[1], values[1])
		// change this to move the token into the header
		Get_Results('/results/'.concat(values[3]));
	}
}


// This was an attempt at a progress bar
function move(total, completed) {
	console.log("MOVE");
	var elem = document.getElementById("myBar");
	elem.style.display = "block";
	var curr = elem.style.width;
	var wid = $(".myBar").width();
	var perwid = $(".myBar").offsetParent().width()
	var per = Math.round(100 * ( wid / perwid));
	console.log(wid);
	console.log(perwid);
	console.log(per);
	console.log(curr);
	if(total != -1){
		var compl_ = Math.floor((completed / total) * 100)
		console.log(compl_);
		if(compl_ > curr){
			elem.style.width = compl_ + "%";
		}
	}
}	
