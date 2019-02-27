// technically this can be minified

$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

function confirm_submission(formId, msg) {
    let form = document.getElementById(formId);
    if (form.checkValidity()) {
        bootbox.confirm(msg, function (result) {
            if (result) {
                form.submit();
            }
        });
    }
    form.classList.add('was-validated');
}

function file_upload(uploadUrl, multiUpload) {
    let dialog = bootbox.dialog({
        message: '<div class="file-upload-container">' +
            '<div class="form-check" style="margin-bottom: 10px">' +
            '  <input class="form-check-input" type="checkbox" id="update-content">' +
            '  <label class="form-check-label" for="update-content">Update content</label>' +
            '</div>' +
            '<input id="file-upload" type="file" ' + (multiUpload ? 'multiple' : '') + '>' +
            '</div>',
        onEscape: function () {
            location.reload();
        }
    });
    dialog.init(function () {
        FilePond.create(document.getElementById("file-upload"));
        FilePond.setOptions({
            allowDrop: false,
            allowReplace: false,
            instantUpload: false,
            server: {
                process: function (_fieldName, file, _metadata, load, error, progress, abort) {
                    const uploadFile = document.getElementById("update-content").checked;
                    return processUploadRequest(uploadUrl + "?update=" + uploadFile, file, load, error, progress, abort);
                }
            }
        });
    })
}

function reportError(title, description) {
    let id = uuid();
    $("#alert-container").append('<div id="' + id + '" class="toast toast-error" role="alert" aria-live="assertive" aria-atomic="true" data-delay="20000">\n' +
        '                <div class="toast-header">\n' +
        '                    <strong class="mr-auto">' + title + '</strong>\n' +
        '                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">\n' +
        '                        <span aria-hidden="true">&times;</span>\n' +
        '                    </button>\n' +
        '                </div>\n' +
        '                <div class="toast-body">' + description + '</div>' +
        '            </div>');
    $('#' + id).toast('show')
}

function reportSuccess(title, description) {
    let id = uuid();
    $("#alert-container").append('<div id="' + id + '" class="toast toast-success" role="alert" aria-live="assertive" aria-atomic="true" data-delay="20000">\n' +
        '                <div class="toast-header">\n' +
        '                    <strong class="mr-auto">' + title + '</strong>\n' +
        '                    <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">\n' +
        '                        <span aria-hidden="true">&times;</span>\n' +
        '                    </button>\n' +
        '                </div>\n' +
        '                <div class="toast-body">' + description + '</div>' +
        '            </div>');
    $('#' + id).toast('show')
}

function processUploadRequest(uploadUrl, file, load, error, progress, abort) {
    const request = new XMLHttpRequest();
    request.open('POST', uploadUrl);
    request.setRequestHeader('Content-Type', 'application/octet-stream');
    request.setRequestHeader('Content-Disposition', `filename="${file.name}"`);

    request.upload.onprogress = (e) => {
        progress(e.lengthComputable, e.loaded, e.total);
    };

    request.onload = function () {
        if (request.status >= 200 && request.status < 300) {
            load(request.response);
        } else {
            console.log("Upload client.errorResponse", request.response);
            let d = JSON.parse(request.responseText);
            reportError(d['title'], d['description']);
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

function uuid() {
    return '_' + Math.random().toString(36).substr(2, 9);
}

function schedule_worker(url) {
    $.ajax({
        type: "POST", url: url, contentType: "application/json", dataType: "json"
    }).done(function (msg) {
        console.info("Worker status", msg);
        reportSuccess("Worker status", "Worker scheduled successfully");
    }).catch(function (err) {
        console.error("Worker error", err.responseText);
        if (err.responseJSON) {
            reportError(err.responseJSON['title'], err.responseJSON['description']);
        } else {
            reportError("Worker error", "An undefined error occurred while attempting to schedule work");
        }
    });
}