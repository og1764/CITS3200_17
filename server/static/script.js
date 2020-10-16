function Copy_To_Clipboard(element) {
  var $temp = $("<textarea>");
  var brRegex = /<br\s*[\/]?>/gi;
  $("body").append($temp);
  $temp.val($(element).html().replace(brRegex, "\r\n")).select();
  document.execCommand("copy");
  $temp.remove();
}

function Get_Function(url, dropzone, token) {
	var xhttp;
	var options = document.getElementById("task").options;
	var index = document.getElementById("task").selectedIndex;
	var network = options[index].text;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("output").innerHTML = xhttp.responseText;
			if (status == "..."){
				document.getElementById("results").innerHTML = "";
			} else {
				document.getElementById("results").innerHTML = '<a href="/getResults/'.concat(token,'" download><button>Download</button></a>');
				document.getElementById("bw-images").innerHTML = '<a href="/getImages/'.concat(token,'" download><button>Download B&W Images</button></a>');
			}
			dropzone.removeAllFiles()
		}else if (this.status == 408){
			// If timeout
			Timeout_Function("/timeout", dropzone, token);
		};
	};
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
	xhttp.setRequestHeader("NETWORK", network);
	xhttp.send();
}

Dropzone.autoDiscover = false;

var myDropzone = new Dropzone(".dropzone", {
  acceptedFiles: ".jpg,.jpeg,.png,.gif,.zip,.tar,.tar.gz",
  autoProcessQueue: false,
  addRemoveLinks: true,
  maxFiles: 10,
  maxFilesize: 10,
  parallelUploads: 10,
  uploadMultiple: true,
  url: "/upload",
  init: function() {
	this.on("successmultiple", function(data, status) {
		document.getElementById("output").innerHTML = "Loading...";
		document.getElementById("file").removeAttribute("hidden");
		Get_Function('/start', this, status);
		Check_Progress(status, -1);
	});
  },
});


function Check_Progress(token, previous) {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			if (this.responseText == 100){
				document.getElementById("file").value = this.responseText;
			} else {
				document.getElementById("file").value = this.responseText;
				Check_Progress(token, this.responseText)
			}
		};
	};
	xhttp.open("GET", '/getProgress/'.concat(token), true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("PREV", previous);
	xhttp.send();
}

function Timeout_Function(url, dropzone, token){
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("output").innerHTML = xhttp.responseText;
			if (status == "..."){
				document.getElementById("results").innerHTML = "";
			} else {
				document.getElementById("results").innerHTML = '<a href="/getResults/'.concat(token,'" download><button>Download</button></a>');
				document.getElementById("bw-images").innerHTML = '<a href="/getImages/'.concat(token,'" download><button>Download B&W Images</button></a>');
			}
			dropzone.removeAllFiles()
		}else if (this.readyState == 4 && this.status == 408) {
			console.log("Timeout Function Hit");
			Timeout_Function(url, dropzone, token);
		};
	};
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
	xhttp.send();
}