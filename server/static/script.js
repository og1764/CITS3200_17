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
				//document.getElementById("bw-images").innerHTML = '<a href="/getImages/'.concat(token,'" download id="bw-dl"><button id="bw-bt">Download B&W Images</button></a>');
				document.getElementById("bw-images").innerHTML = '<button id="bw-bt" onclick=B_W_Download("/getImages/'.concat(token,'")>Download B&W Images</button>');
			}
			dropzone.removeAllFiles()
		}else if (this.status == 408){
			// If timeout
			Timeout_Function("/timeout", dropzone, token, "-1", "0");
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
		document.getElementById("bw-images").innerHTML = '<a></a>';
		document.getElementById("output").innerHTML = "Loading...";
		document.getElementById("file").removeAttribute("hidden");
		Get_Function('/start', this, status);
		Check_Progress(status, "-1", "0");
	});
  },
});


function Check_Progress(token, previous, wait) {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			var resp_text = this.responseText;
			var splitted = resp_text.split(",")
			if (splitted[0] == 100){
				document.getElementById("file").value = splitted[0];
			} else {
				document.getElementById("file").value = splitted[0];
				Check_Progress(token, splitted[0], splitted[1]);
			}
		};
	};
	xhttp.open("GET", '/getProgress/'.concat(token), true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
	xhttp.setRequestHeader("PREV", previous);
	xhttp.setRequestHeader("WAIT", wait);
	xhttp.send();
}

function Timeout_Function(url, dropzone, token, previous, wait){
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("output").innerHTML = xhttp.responseText;
			if (status == "..."){
				document.getElementById("results").innerHTML = "";
			} else {
				document.getElementById("results").innerHTML = '<a href="/getResults/'.concat(token,'" download><button>Download</button></a>');
				document.getElementById("bw-images").innerHTML = '<a href="/getImages/'.concat(token,'" download id="bw-dl"><button id="bw-bt">Download B&W Images</button></a>');
			}
			dropzone.removeAllFiles()
		}else if (this.readyState == 4 && this.status == 408) {
			console.log("Timeout Function Hit");
			var resp_text = this.responseText;
			var splitted = resp_text.split(",")
			Timeout_Function(url, dropzone, token, splitted[0], splitted[1]);
		};
	};
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
	xhttp.setRequestHeader("PREV", previous);
	xhttp.setRequestHeader("WAIT", wait);
	xhttp.send();
}

function B_W_Download(url){
	document.getElementById("bw-bt").innerHTML = "Processing...";
	Get_B_W(url);
}


function Get_B_W(url) {

	var a = document.createElement("a");
	document.body.appendChild(a);
	a.style = "display:none";
	a.href = url;
	a.download = "B_W_images.zip";
	a.click();
	a.remove();
	
	var xhttp = new XMLHttpRequest();
	xhttp.open('GET', url, true);
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("bw-bt").innerHTML = "Download B&W Images";
		}
	}
	xhttp.send();	
}
