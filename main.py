import os
import json
import contextlib

import click

from subprocess import Popen

cur_dir = os.path.dirname(os.path.abspath(__file__))


def add_services_json(process, dir) -> None:
    with open(f'{cur_dir}/services.json', 'r+') as f:
        services = json.load(f)
        services["process_ids"][dir] = process.pid
        f.seek(0)
        json.dump(services, f, indent=4)
        f.truncate()


def remove_services_json(dir) -> None:
    with open(f'{cur_dir}/services.json', 'r+') as f:
        services = json.load(f)
        with contextlib.suppress(ProcessLookupError):
            os.kill(services["process_ids"][dir], 9)
        services["process_ids"].pop(dir)
        f.seek(0)
        json.dump(services, f, indent=4)
        f.truncate()


def load_service(dir) -> None:
    with open(f'{cur_dir}/services/{dir}/service.json', 'r+') as f:
        return json.loads(f.read())
       

def load_all_services() -> None:
    for dir in os.listdir(f'{cur_dir}/services'):
        if not os.path.isdir(os.path.join(f'{cur_dir}/services', dir)) and \
          not os.path.exists(os.path.join(f'{cur_dir}/services', dir, 'service.json')):
            continue
        data = load_service(dir)

        if data['language'] == 'python':
            process = Popen(['python3', f'{cur_dir}/services/{dir}/bot.py'])
        elif data['language'] == 'javascript':
            process = Popen(['node', '--es-module-specifier-resolution=node', f'{cur_dir}/services/{dir}/src/server.js'])

        add_services_json(process, dir)


@click.group()
@click.option(
    '-s', '--service', default='all',
    help='Service to start/turn off.'
)
@click.pass_context
def service(ctx, service) -> None:
    """
    Service manager.
    """
    pass


@service.command()
@click.pass_context
def services(ctx) -> None:
    """
    List of running services.
    """
    with open(f'{cur_dir}/services.json', 'r') as f:
        services = json.load(f)

    if len(services["process_ids"]) == 0:
        return click.echo('No services running.')

    for dir, pid in services["process_ids"].items():
        click.echo(f'Service {dir} -> {pid}')


@service.command()
@click.pass_context
def start(ctx) -> None:
    """
    Start current service/all services.
    """
    if ctx.parent.params['service'] == 'all':
        return load_all_services()

    data = load_service(ctx.parent.params['service'])

    if data['language'] == 'python':
        process = Popen(['python3', f'{cur_dir}/services/{ctx.parent.params["service"]}/bot.py'])
    elif data['language'] == 'javascript':
        process = Popen(['node', '--es-module-specifier-resolution=node', f'{cur_dir}/services/{ctx.parent.params["service"]}/src/server.js'])
        
    add_services_json(process, ctx.parent.params["service"])


@service.command()
@click.pass_context
def stop(ctx) -> None:
    """
    Stop current service/all services.
    """
    if ctx.parent.params['service'] == 'all':
        with open(f'{cur_dir}/services.json', 'r+') as f:
            services = json.load(f)
            for service in services["process_ids"]:
                with contextlib.suppress(ProcessLookupError):
                    os.kill(services["process_ids"][service], 9)
            f.seek(0)
            json.dump({"process_ids": {}}, f, indent=4)
            f.truncate()
        return None
    remove_services_json(ctx.parent.params["service"])


if __name__ == '__main__':
    service()
