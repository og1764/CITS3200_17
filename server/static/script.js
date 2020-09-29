function copyToClipboard(element) {
  var $temp = $("<textarea>");
  var brRegex = /<br\s*[\/]?>/gi;
  $("body").append($temp);
  $temp.val($(element).html().replace(brRegex, "\r\n")).select();
  document.execCommand("copy");
  $temp.remove();
}

function httpGetAsync(theUrl, callback)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
			callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}

function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

function loadDoc(url, cFunction) {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var splt = xhttp.responseText.split(/\r?\n/);
			var splt_one = splt[0] + '';
			var splt_two = splt[1] + '';
			var splt_thr = splt[2] + '';
			var splt_for = splt[3] + '';
						
			console.log(splt);
			console.log(splt_one);
			console.log(xhttp.responseText);
			_state = splt_one.split(" ")[1];
			_total = splt_two.split(" ")[1];
			_count = splt_thr.split(" ")[1];
			_ident = splt_for.split(" ")[1];
			console.log(_state);
			console.log(_total);
			sleep(3000);
			cFunction(this, [_state, _total, _count, _ident]);
		}
	};
	xhttp.open("GET", url, true);
	xhttp.send();
}

function Get_Progress(xhttp, values) {
	if (values[1] != values[2]){
		console.log(values);
		sleep(3000);
		loadDoc('/progress/'.concat(values[3]), Get_Progress);
	} else {
		Get_Results('/results/'.concat(values[3]));
	}
}

function Get_Results(url) {
	var xhttpTWO;
	xhttpTWO = new XMLHttpRequest();
	xhttpTWO.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
			document.getElementById("output").innerHTML = xhttpTWO.responseText;
			console.log(status);
			console.log(xhttpTWO.responseText);
		}
	};
	xhttpTWO.open("GET", url, true);
	xhttpTWO.setRequestHeader('x-customtoken', '0');
	xhttpTWO.send();
}

function Download_File() {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.setRequestHeader('x-customtoken', '1');
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
		}
	};
	xhttp.open("GET", url, true);
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
		//processFiles();
		var prefix = '/progress/';
		//@app.route('/progress/<token>', methods=["GET"])
		var _state = "";
		var _total = 0;
		var _count = 0;
		var _ident = "";
		sleep(5000);
		loadDoc('/progress/'.concat(status), Get_Progress);
		
		//document.getElementById("output").innerHTML = status;
		document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
		this.removeAllFiles()
	});
  },
});

//var el = document.getElementById("classify");
//el.addEventListener("click", removeFunction);
