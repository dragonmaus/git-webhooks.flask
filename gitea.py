import hmac
import os.path
from functools import wraps
from subprocess import PIPE, run
from tempfile import SpooledTemporaryFile, TemporaryDirectory

import requests
import uritemplate
from flask import Flask, request

from common import kebab2normal, secret, status

app = Flask(__name__)

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = hmac.new(secret.api_key, msg=request.get_data(), digestmod='sha256').hexdigest()
        if request.headers.get('X-Gitea-Signature') != signature:
            return status(401)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/push', methods=['POST'])
@api_key_required
def push():
    if not request.is_json:
        return status(400)
    data = request.json

    if not ('ref' in data and data['ref'].startswith('refs/tags/')):
        return status(200)

    base = data['compare_url'] + 'api/v1'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'token ' + secret.token.gitea,
    }
    repo = data['repository']

    # get tag information
    uri = uritemplate.expand(base + '/repos/{owner}/{repo}/git/tags/{sha}',
                             owner=repo['owner']['username'],
                             repo=repo['name'],
                             sha=data['after'])
    r = requests.get(uri, headers=headers)
    if r.status_code != 200:
        return status(500, message=f'error fetching "{uri}"')

    tag = r.json()

    # create release
    uri = uritemplate.expand(base + '/repos/{owner}/{repo}/releases',
                             owner=repo['owner']['username'],
                             repo=repo['name'])
    payload = {
        'body': tag['message'],
        'draft': False,
        'name': kebab2normal(repo['name']) + ' ' + tag['tag'],
        'prerelease': False,
        'tag_name': tag['tag'],
        'target_commitish': repo['default_branch'],
    }
    r = requests.post(uri, headers=headers, json=payload)
    if r.status_code != 201:
        return status(500, message=f'error fetching "{uri}"')

    release = r.json()

    # create release zip
    with SpooledTemporaryFile() as f:
        with TemporaryDirectory() as d:
            p = run(['git', 'clone', repo['clone_url'], d])
            if p.returncode != 0:
                return status(500, message='error cloning repository')

            cmd = ['sh', os.path.join(d, '.bin', 'release.sh'), tag['tag']]
            if not os.path.exists(cmd[1]):
                cmd = ['git', 'archive', '--format=zip', tag['tag']]

            p = run(cmd, stdout=PIPE, cwd=d)
            if p.returncode != 0:
                return status(500, message='error creating archive')

            b = p.stdout

    # upload release zip
    uri = uritemplate.expand(base + '/repos/{owner}/{repo}/releases/{id}/assets?name={name}',
                             owner=repo['owner']['username'],
                             repo=repo['name'],
                             id=release['id'],
                             name=repo['name'] + '.zip')
    payload = {
        'attachment': (repo['name'] + '.zip', b, 'application/zip'),
    }
    r = requests.post(uri, headers=headers, files=payload)
    if r.status_code != 201:
        return status(500, message='error uploading archive')

    return status(200, message='release created')
