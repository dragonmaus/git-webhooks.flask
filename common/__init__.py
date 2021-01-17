from flask import current_app, jsonify, make_response
from werkzeug.http import HTTP_STATUS_CODES as status_codes

__all__ = ['kebab2normal', 'shellify', 'status']

def kebab2normal(s):
    return ' '.join(x.capitalize() for x in s.split('-'))

def shellify(data):
    text = ''
    for k, v in data.items():
        text += py2sh(k, v)
    return current_app.response_class(text, mimetype='text/x-shellscript')

def status(code, headers={}, **kwargs):
    payload = {'status': status_codes[code]}
    payload.update(**kwargs)
    return make_response((jsonify(payload), code, headers))

# helpers

def py2sh(key, value, prefix=''):
    result = ''
    if type(value) == dict:
        for k, v in value.items():
            result += py2sh(k, v, f'{prefix}{key}_')
    elif type(value) == list:
        for i in range(len(value)):
            result += py2sh(i, value[i], f'{prefix}{key}_')
    else:
        if type(value) == bool:
            value = str(value).lower()
        result = f'{prefix}{key}="{shellquote(value)}"\n'
    return result

shellquote_table = str.maketrans(dict([(c, '\\' + c) for c in '"$\\`']))

def shellquote(value):
    return str(value).translate(shellquote_table)
