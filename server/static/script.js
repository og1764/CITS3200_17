/**
    * Copy the classfied result.
    * @param    {String}    element     The classified infomation.
*/
function Copy_To_Clipboard(element) {
    var $temp = $("<textarea>");
    var brRegex = /<br\s*[\/]?>/gi;
    $("body").append($temp);
    $temp.val($(element).html().replace(brRegex, "\r\n")).select();
    document.execCommand("copy");
    $temp.remove();
}

/**
    * Getting the processed result from start_processing() that is implemented in app.py
    * Outputting the result in the output zone.
    * Dynamically create two buttons, "Download" and "Download B&W Image" that allows user to download the classfied result as a text file and processed image files.
    * @param    {String}    url         Base URL.
    * @param    {String}    dropzone    Dropzone object.
    * @param    {String}    token       Unique Identifier.
*/
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
                document.getElementById("bw-images").innerHTML = '<button id="bw-bt" onclick=B_W_Download("/getImages/'.concat(token,'")>Download B&W Images</button>');
                document.getElementById("progress-container").style.display = "none";
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
    acceptedFiles: "image/*,.zip,.tar,.tar.gz",
    autoProcessQueue: false,
    addRemoveLinks: true,
    maxFiles: 10,
    maxFilesize: 10,
    parallelUploads: 10,
    uploadMultiple: true,
    url: "/upload",
    init: function() {
        this.on("successmultiple", function(data, status) {
            Get_Function('/start', this, status);
            Check_Progress(status, "-1", "0");
        });
    },
});

/**
    * Gets progress of request based on the token, and updates the progress bar.
    * @param    {String}    token       Unique Identifier.
    * @param    {Int}       previous    Progress at previous request.
    * @param    {Int}       wait        Time the previous request waited for.
*/
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
                document.getElementById("prog-lbl").innerHTML = splitted[2];
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

/**
    * Gets result of request in case of a timeout. This is a backup function and should never get called.
    * @param    {String}    url         Timeout URL.
    * @param    {Object}    dropzone    Dropzone object.
    * @param    {String}    token       Unique Identifier.
    * @param    {Int}       previous    Progress at previous request.
    * @param    {Int}       wait        Time the previous request waited for.
*/
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
                document.getElementById("bw-images").innerHTML = '<button id="bw-bt" onclick=B_W_Download("/getImages/'.concat(token,'")>Download B&W Images</button>');
                document.getElementById("progress-container").style.display = "none";
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

/**
    * Download the files that were processed for classification.
    * @param    {String}    url         URL to download images.
*/
function B_W_Download(url){
    document.getElementById("bw-bt").innerHTML = "Processing...";
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


/**
    * Initialise the Dropzone upload, and reveal the progress bar.
*/
function to_upload(){
    document.getElementById("progress-container").style.display = "block";
    document.getElementById("prog-lbl").innerHTML = "Uploading... ";
    document.getElementById("bw-images").innerHTML = '<a></a>';
    document.getElementById("output").innerHTML = "Loading...";
    Dropzone.forElement('.dropzone').processQueue()
}
