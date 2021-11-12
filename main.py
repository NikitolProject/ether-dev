import os
import json
import contextlib

import click

from subprocess import Popen


def add_services_json(process, dir) -> None:
    with open('services.json', 'r+') as f:
        services = json.load(f)
        services["process_ids"][dir] = process.pid
        f.seek(0)
        json.dump(services, f, indent=4)
        f.truncate()


def remove_services_json(dir) -> None:
    with open('services.json', 'r+') as f:
        services = json.load(f)
        with contextlib.suppress(ProcessLookupError):
            os.kill(services["process_ids"][dir], 9)
        services["process_ids"].pop(dir)
        f.seek(0)
        json.dump(services, f, indent=4)
        f.truncate()


def load_all_services() -> None:
    for dir in os.listdir('services'):
        if not os.path.isdir(os.path.join('services', dir)) and \
          not os.path.exists(os.path.join('services', dir, 'service.json')):
            continue
        process = Popen(['python3', f'services/{dir}/bot.py'])
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
    with open('services.json', 'r') as f:
        services = json.load(f)

    if len(services["process_ids"]) == 0:
        click.echo('No services running.')
        return None

    for dir, pid in services["process_ids"].items():
        click.echo(f'Service {dir} -> {pid}')


@service.command()
@click.pass_context
def start(ctx) -> None:
    """
    Start current service/all services.
    """
    if ctx.parent.params['service'] == 'all':
        load_all_services()
    else:
        process = Popen(['python3', f'services/{ctx.parent.params["service"]}/bot.py'])
        add_services_json(process, ctx.parent.params["service"])


@service.command()
@click.pass_context
def stop(ctx) -> None:
    """
    Stop current service/all services.
    """
    if ctx.parent.params['service'] == 'all':
        with open('services.json', 'r+') as f:
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
