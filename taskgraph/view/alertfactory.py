from enum import Enum


class Alert:

    Types = Enum('Types', 'Success Info Warning Error')

    css_types = {Types.Success: 'alert-success',
                 Types.Info: 'alert-info',
                 Types.Warning: 'alert-warning',
                 Types.Error: 'alert-danger'}

    def __init__(self, alert_type, message, name='', css_container_class=''):
        if not name:
            name = alert_type.name
        self.css_class = Alert.css_types[alert_type]
        self.css_container_class = css_container_class
        self.name = name
        self.message = message


def success(message, name='', css_container_class=''):
    return Alert(Alert.Types.Success, message, name, css_container_class)


def info(message, name='', css_container_class=''):
    return Alert(Alert.Types.Info, message, name, css_container_class)


def warning(message, name='', css_container_class=''):
    return Alert(Alert.Types.Warning, message, name, css_container_class)


def error(message, name='', css_container_class=''):
    return Alert(Alert.Types.Error, message, name, css_container_class)