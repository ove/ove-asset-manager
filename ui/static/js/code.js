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