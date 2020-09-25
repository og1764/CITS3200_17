function processFiles() {
    $.get("/result", function(data, status){
		document.getElementById("p1").innerHTML = data;
		document.getElementById("p2").innerHTML = '<a href="/getResults" download><button>Download</button></a>';
	});
}

function copyToClipboard(element) {
    var $temp = $("<input>");
    $("body").append($temp);
    $temp.val($(element).text()).select();
    document.execCommand("copy");
    $temp.remove();
}

Dropzone.autoDiscover = false;

var myDropzone = new Dropzone(".dropzone", {
  addRemoveLinks: true,
  removedfile: function(file) {
    var fileName = file.name;

    $.ajax({
      type: 'POST',
      url: '../static/upload.php',
      data: {name: fileName,request: 'delete'},
    });

    var _ref;
    return (_ref = file.previewElement) != null ? _ref.parentNode.removeChild(file.previewElement) : void 0;
   }
});

function removeFunction() {
    Dropzone.forElement(".dropzone").removeAllFiles(true);
};

var el = document.getElementById("classify");
el.addEventListener("click", removeFunction);  
