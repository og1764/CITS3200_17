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
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			document.getElementById("output").innerHTML = xhttp.responseText;
			//document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
			if (status == "..."){
				document.getElementById("results").innerHTML = "";
			} else {
				// might have to change this to calling a function if it still doesnt like the URL
				document.getElementById("results").innerHTML = '<a href="/getResults/'.concat(token,'" download><button>Download</button></a>');
			}
			dropzone.removeAllFiles()
		};
	};
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.setRequestHeader("TOKEN", token);
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
		Check_Progress(status);
	});
  },
});


function Check_Progress(token) {
	var xhttp;
	xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
			if (this.responseText == 100){
				//window.alert(this.responseText);
				//window.alert("status next");
				//window.alert(status);
				document.getElementById("file").value = this.responseText;
			} else {
				//window.alert(xhttp.responseText);
				//window.alert("status next");
				//window.alert(status);
				document.getElementById("file").value = this.responseText;
				Check_Progress(token)
			}
		};
	};
	xhttp.open("GET", '/getProgress/'.concat(token), true);
	xhttp.setRequestHeader("Access-Control-Allow-Headers", "*");
	xhttp.send();
}
