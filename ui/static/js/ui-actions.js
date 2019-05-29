// technically this can be minified

/*global bootbox FilePond:true*/
/*eslint no-undef: "error"*/

$(document).ready(function () {
    $("[data-toggle='tooltip']").tooltip();
});

function confirmSubmission(formId, msg) {
    let form = document.getElementById(formId);
    if (form.checkValidity()) {
        bootbox.confirm(msg, function (result) {
            if (result) {
                form.submit();
            }
        });
    }
    form.classList.add("was-validated");
}

function processUploadRequest(uploadUrl, file, load, error, progress, abort) {
    const request = new XMLHttpRequest();
    request.open("POST", uploadUrl);
    request.setRequestHeader("Content-Type", "application/octet-stream");
    request.setRequestHeader("Content-Disposition", `filename='${file.name}'`);

    request.upload.onprogress = (e) => {
        progress(e.lengthComputable, e.loaded, e.total);
    };

    request.onload = function () {
        if (request.status >= 200 && request.status < 300) {
            load(request.response);
        } else {
            let d = JSON.parse(request.responseText);
            reportError(d["title"], d["description"]);
            error("Server error");
        }
    };

    request.send(file);

    return {
        abort: () => {
            request.abort();
            abort();
        }
    };
}

function fileUpload(uploadUrl, multiUpload) {
    let dialog = bootbox.dialog({
        message: "<div class='file-upload-container'>" +
            "<span data-toggle='tooltip' data-placement='top' data-html='true' title='Note: The upload is not complete until the upload box " +
            "becomes green. If you wait at 100% for a long time it may be because the content is still being uploaded to the object store in the asset " +
            "manager.'>\n" +
            "   <i class='fas fa-exclamation-circle icon-error'></i>\n" +
            "</span>" +
            "<div class='form-check' style='margin-bottom: 10px'>" +
            "  <input class='form-check-input' type='checkbox' id='update-content'>" +
            "  <label class='form-check-label' for='update-content'>Update content</label>" +
            "</div>" +
            "<input id='file-upload' type='file' " + (multiUpload ? "multiple" : "") + ">" +
            "</div>",
        onEscape: function () {
            location.reload();
        }
    });
    dialog.init(function () {
        FilePond.create(document.getElementById("file-upload"));
        FilePond.setOptions({
            allowDrop: true,
            allowReplace: false,
            instantUpload: false,
            server: {
                process: function (_fieldName, file, _metadata, load, error, progress, abort) {
                    const uploadFile = document.getElementById("update-content").checked;
                    return processUploadRequest(uploadUrl + "?update=" + uploadFile, file, load, error, progress, abort);
                }
            }
        });
    });
}

function uuid() {
    return "_" + Math.random().toString(36).substr(2, 9);
}

function reportError(title, description) {
    let id = uuid();
    $("#alert-container").append("<div id='" + id + "' class='toast toast-error' role='alert' aria-live='assertive' aria-atomic='true' data-delay='20000'>\n" +
        "                <div class='toast-header'>\n" +
        "                    <strong class='mr-auto'>" + title + "</strong>\n" +
        "                    <button type='button' class='ml-2 mb-1 close' data-dismiss='toast' aria-label='Close'>\n" +
        "                        <span aria-hidden='true'>&times;</span>\n" +
        "                    </button>\n" +
        "                </div>\n" +
        "                <div class='toast-body'>" + description + "</div>" +
        "            </div>");
    $("#" + id).toast("show");
}

function reportSuccess(title, description) {
    let id = uuid();
    $("#alert-container").append("<div id='" + id + "' class='toast toast-success' role='alert' aria-live='assertive' aria-atomic='true' data-delay='20000'>\n" +
        "                <div class='toast-header'>\n" +
        "                    <strong class='mr-auto'>" + title + "</strong>\n" +
        "                    <button type='button' class='ml-2 mb-1 close' data-dismiss='toast' aria-label='Close'>\n" +
        "                        <span aria-hidden='true'>&times;</span>\n" +
        "                    </button>\n" +
        "                </div>\n" +
        "                <div class='toast-body'>" + description + "</div>" +
        "            </div>");
    $("#" + id).toast("show");
}

function postWorkerParams(url, params) {
    return $.ajax({type: "POST", url: url, contentType: "application/json", dataType: "json", data: JSON.stringify(params)}).done(function (msg) {
        reportSuccess("Worker status", "Worker scheduled successfully");
    }).catch(function (err) {
        if (err.responseJSON) {
            reportError(err.responseJSON["title"], err.responseJSON["description"]);
        } else {
            reportError("Worker error", "An undefined error occurred while attempting to schedule work");
        }
    });
}