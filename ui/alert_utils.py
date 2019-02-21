from falcon import Response


def report_error(resp: Response, title: str = "Error", description: str = ""):
    report_alert(type="error", resp=resp, title=title, description=description)


def report_info(resp: Response, title: str = "Info", description: str = ""):
    report_alert(type="info", resp=resp, title=title, description=description)


def report_success(resp: Response, title: str = "Success", description: str = ""):
    report_alert(type="success", resp=resp, title=title, description=description)


def report_warning(resp: Response, title: str = "Warning", description: str = ""):
    report_alert(type="warning", resp=resp, title=title, description=description)


def report_alert(type: str, resp: Response, title: str = "Error", description: str = ""):
    if not hasattr(resp, "alerts"):
        resp.alerts = []

    resp.alerts.append({
        "title": title,
        "type": type,
        "description": description
    })
