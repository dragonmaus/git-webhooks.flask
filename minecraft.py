from operator import itemgetter

from flask import Flask, jsonify, request
from mcstatus import MinecraftServer

from common import shellify

app = Flask(__name__)

@app.route('/online', methods=['POST'])
def online():
    server = MinecraftServer.lookup(request.form['server'])
    data = {
        'online': False,
        'server': {
            'host': server.host,
            'port': server.port,
        },
    }
    try:
        server.ping()
        data['online'] = True
    except:
        pass
    fmt = request.form.get('format', 'json')
    if fmt == 'json':
        return jsonify(data)
    elif fmt == 'shell':
        return shellify(data)

@app.route('/status', methods=['POST'])
def status():
    server = MinecraftServer.lookup(request.form['server'])
    data = {
        'online': False,
        'server': {
            'host': server.host,
            'port': server.port,
        },
    }
    try:
        # check if server is alive
        server.ping()
        data['online'] = True

        # try to get basic information
        status = server.status()
        if 'favicon' in request.form:
            data['favicon'] = status.favicon
        data['latency'] = status.latency
        data['motd'] = status.description.get('text', 'A Minecraft Server')
        data['players'] = {
            'max': status.players.max,
            'names': sorted([player.name for player in status.players.sample or []]),
            'online': status.players.online,
        }
        data['software'] = {
            'protocol': status.version.protocol,
            'version': status.version.name,
        }

        # get more specific/accurate information if query is enabled serverside
        query = server.query()
        data['map'] = query.map
        data['motd'] = query.motd
        data.setdefault('players', {})
        data['players']['max'] = query.players.max
        data['players']['names'] = sorted(query.players.names)
        data['players']['online'] = query.players.online
        data.setdefault('software', {})
        data['software']['brand'] = query.software.brand
        data['software']['plugins'] = sorted(query.software.plugins)
        data['software']['version'] = query.software.version
    except:
        pass
    fmt = request.form.get('format', 'json')
    if fmt == 'json':
        return jsonify(data)
    elif fmt == 'shell':
        return shellify(data)
