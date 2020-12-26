from flask import jsonify, make_response
from werkzeug.http import HTTP_STATUS_CODES as status_codes

__all__ = ['kebab2normal', 'status']

def kebab2normal(s):
    return ' '.join(x.capitalize() for x in s.split('-'))

def status(code, headers={}, **kwargs):
    payload = {'status': status_codes[code]}
    payload.update(**kwargs)
    return make_response((jsonify(payload), code, headers))
