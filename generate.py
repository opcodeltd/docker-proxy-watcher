#!/usr/bin/env python3

import json
import jinja2
import hashlib
import subprocess

if __name__ == '__main__':
    with open('vhost_template.jinja2') as fh:
        template = jinja2.Template(fh.read())

    with open('info.json') as fh:
        data = json.load(fh)

    vhosts = {}

    for container in sorted(data, key=lambda c: c['Name']):
        print(container['Name'])
        if not container['Labels']:
            continue

        if container['Labels'].get('com.docker.compose.oneoff', 'False') == 'True':
            continue

        for key, value in container['Labels'].items():
            if not key.startswith('nz.opdev.m'):
                continue

            vhost = dict(
                server_name = '.'.join(reversed(key.split('.'))),
            )
            vhost['upstream_name'] = 'docker_' + vhost['server_name'].replace('.', '_').replace('-', '_')
            matches = [x for x in container['Addresses'] if x['Port'] == value]
            if len(matches) != 1:
                continue

            vhost['ports'] = [matches[0]['HostPort']]

            print("\t%s = %s => %s" % (key, value, vhost['ports'][0]))

            if vhost['server_name'] in vhosts:
                vhosts[vhost['server_name']]['ports'].extend(vhost['ports'])
            else:
                vhosts[vhost['server_name']] = vhost

    existing_hash = None
    try:
        with open('nginx.conf', 'r') as fh:
            existing_hash = hashlib.sha1(fh.read().encode('ascii'))
    except FileNotFoundError:
        pass

    nginx_config = template.render(vhosts=vhosts.values())
    new_hash = hashlib.sha1(nginx_config.encode('ascii'))

    if existing_hash and existing_hash.hexdigest() == new_hash.hexdigest():
        print("No change, not writing")
    else:
        print("Writing nginx.conf")
        with open('nginx.conf', 'w') as fh:
            fh.write(nginx_config)
        subprocess.check_call(['sudo', '/usr/sbin/nginx', '-s', 'reload'])
