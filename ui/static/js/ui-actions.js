$(document).ready(function () {
    $("[data-toggle='tooltip']").tooltip();
});

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

function processUploadRequest(uploadUrl, file, load, error, progress, abort, updateFlag) {
    const request = new XMLHttpRequest();
    request.open("POST", uploadUrl + "?update=" + updateFlag + "&filename=" + encodeURIComponent(file.name));
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

function postWorkerParams(url, params) {
    return $.ajax({type: "POST", url: url, contentType: "application/json", dataType: "json", data: JSON.stringify(params)}).done(function () {
        reportSuccess("Worker status", "Worker scheduled successfully");
    }).catch(function (err) {
        if (err.responseJSON) {
            reportError(err.responseJSON["title"], err.responseJSON["description"]);
        } else {
            reportError("Worker error", "An undefined error occurred while attempting to schedule work");
        }
    });
}