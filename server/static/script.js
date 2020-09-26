function copyToClipboard(element) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val($(element).text()).select();
    document.execCommand("copy");
    $temp.remove();
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
		document.getElementById("output").innerHTML = status;
		document.getElementById("results").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
		this.removeAllFiles()
	});
  },
});

//var el = document.getElementById("classify");
//el.addEventListener("click", removeFunction);
