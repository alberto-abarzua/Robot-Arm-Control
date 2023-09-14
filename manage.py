#!/usr/bin/env python3

import argparse
import subprocess
import os
import time
import signal
import threading
import sys

from typing import List
from pathlib import Path
# General functions

CURRENT_FILE_PATH = Path(__file__).parent.absolute()

DOCKER_SERVICES = CURRENT_FILE_PATH/'docker_services'


# Docker helper commands

def get_file_list(files: List[str]):
    file_list = []
    for f in files:
        file_list.append('-f')
        file_path = DOCKER_SERVICES/f
        file_list.append(str(file_path))
    return file_list


def dcr(file_str: str, command: str, env={}):
    command_list = command.split(' ')
    file_path = DOCKER_SERVICES/file_str

    subprocess.check_call(
        ['docker', 'compose', '-f', str(file_path), 'run', '--rm', *command_list], env={**os.environ, **env})


def dcu(files: List[str], env: dict = {}):
    file_list = get_file_list(files)
    subprocess.check_call(
        ['docker', 'compose', *file_list, 'up'], env={**os.environ, **env})


def dcd(files: List[str]):
    file_list = get_file_list(files)

    subprocess.check_call(
        ['docker', 'compose', *file_list, 'down', '--remove-orphans'])


def dcb(files: List[str], no_cache=False):
    file_list = get_file_list(files)
    if no_cache:
        subprocess.check_call(
            ['docker', 'compose', *file_list, 'build', '--no-cache'], env={**os.environ})
    else:
        subprocess.check_call(
            ['docker', 'compose', *file_list, 'build'], env={**os.environ})


def get_ip(**kwargs):
    return subprocess.getoutput("hostname -I | awk '{print $1}'").strip()


def source_env(file_path):
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            # Remove the 'export ' prefix if present
            if line.startswith('export '):
                line = line[7:]
            key, value = line.split('=', 1)
            os.environ[key] = value
# commands


def build_firmware(**kwargs):
    dcr('firmware.yaml', 'firmware build')


def down(**kwargs):
    dcd(['firmware.yaml', 'controller.yaml', 'backend.yaml',
        'frontend.yaml', 'unity_webgl_server.yaml'])


def build(**kwargs):
    no_cache = kwargs['no_cache']
    if no_cache:
        dcb(['firmware.yaml', 'controller.yaml',
            'backend.yaml', 'frontend.yaml'], no_cache=True)
    else:
        dcb(['firmware.yaml', 'controller.yaml', 'backend.yaml', 'frontend.yaml'])


def build_esp(**kwargs):
    os.environ['CONTROLLER_SERVER_HOST'] = get_ip()
    source_env('.env')
    subprocess.check_call(['./firmware/entrypoint_esp.sh'])


def format_code(**kwargs):
    dcr('firmware.yaml', 'firmware format')
    dcr('controller.yaml', 'controller pdm run format')
    dcr('backend.yaml', 'backend pdm run format')
    dcr('frontend.yaml', 'frontend npm run format')
    dcd(['firmware.yaml', 'controller.yaml', 'backend.yaml', 'frontend.yaml'])


def lint(**kwargs):

    dcr('controller.yaml', 'controller pdm run lint')
    dcr('backend.yaml', 'backend pdm run lint')
    dcr('frontend.yaml', 'frontend npm run lint')
    dcd(['firmware.yaml', 'controller.yaml', 'backend.yaml', 'frontend.yaml'])


def test(**kwargs):
    # build_firmware()
    dcu(['controller.yaml', 'firmware.yaml'], env={
        "ESP_CONTROLLER_SERVER_HOST": "controller", "CONTROLLER_COMMAND": "test"})
    dcd(['controller.yaml', 'firmware.yaml'])


def build_flash_esp(**kwargs):
    os.environ['ESP_CONTROLLER_SERVER_HOST'] = get_ip()
    print("Requires idf.py to be installed and environment variables to be set")
    print("Also requires to export variables from .env file -->\n\t source .env")
    if 'IDF_PATH' not in os.environ:
        print("IDF_PATH is not set")
        exit(1)

    subprocess.check_call(['rm', '-rf', 'build'], cwd='firmware')
    subprocess.check_call(['idf.py', 'build', 'flash','monitor'],
                          cwd='firmware', env=os.environ)


def test_esp(**kwargs):
    # build_flash_esp()
    dcu(['controller.yaml' ], env={ "CONTROLLER_COMMAND": "test"})
    
    # subprocess.check_call(['idf.py', 'monitor'], cwd='firmware', env={
    #                       "ESP_CONTROLLER_SERVER_HOST": get_ip()})



def gdb(**kwargs):
    # subprocess.check_call(
    #     ['docker', 'compose', 'run', '--rm', 'firmware', 'gdb'])
    dcr('firmware.yaml', 'firmware gdb')


def runserver(**kwargs):

    esp = kwargs['esp']
    if esp:
        print("Running server for the esp-32")
        dcu(['backend.yaml', 'unity_webgl_server.yaml', 'frontend.yaml'],
            env={"ESP_CONTROLLER_SERVER_HOST": get_ip()})
    else:
        print('Running server for the linux platform')
        dcu(['backend.yaml', 'unity_webgl_server.yaml',
            'frontend.yaml', 'firmware.yaml'])



def shell(**kwargs):
    container_name = kwargs['container']
    if container_name == 'firmware':
        dcr('firmware.yaml', 'firmware /bin/sh')
    elif container_name == 'controller':
        dcr('controller.yaml', 'controller /bin/sh')
    elif container_name == 'backend':
        dcr('backend.yaml', 'backend /bin/sh')
    elif container_name == 'frontend':
        dcr('frontend.yaml', 'frontend /bin/sh')
    elif container_name == 'unity_webgl_server':
        dcr('unity_webgl_server.yaml', 'unity_webgl_server /bin/sh')
    else:
        print(f"Unknown container: {container_name}")
        exit(1)

def handle_sigint(signum, frame):
    down()
    print("Containers stopped. Exiting...")
    exit(0)


def main(**kwargs):
    source_env('.env')
    signal.signal(signal.SIGINT, handle_sigint)

    parser = argparse.ArgumentParser(
        description='Manage the build, test, and deployment process.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command')

    parser_buildf = subparsers.add_parser(
        'buildf', help='Build the firmware for linux platform')
    parser_buildf.set_defaults(func=build_firmware)

    parser_build = subparsers.add_parser(
        'build', help='Build all docker images')
    parser_build.set_defaults(func=build)

    parser_build.add_argument(
        '--no-cache', action='store_true', help='Build all docker images without cache')

    parser_build_esp = subparsers.add_parser(
        'build-esp', help='Build the firmware for esp32 platform')
    parser_build_esp.set_defaults(func=build_esp)

    parser_format = subparsers.add_parser(
        'format', help='Format all code')
    parser_format.set_defaults(func=format_code)

    parser_lint = subparsers.add_parser('lint', help='Lint all code')
    parser_lint.set_defaults(func=lint)

    parser_test = subparsers.add_parser('test', help='Run all tests')
    parser_test.set_defaults(func=test)

    parser_test_esp = subparsers.add_parser(
        'test-esp', help='Run all tests on esp32')
    parser_test_esp.set_defaults(func=test_esp)

    parser_gdb = subparsers.add_parser(
        'gdb', help='Run gdb for firmware')
    parser_gdb.set_defaults(func=gdb)

    parser_runserver = subparsers.add_parser(
        'runserver', help='Run server')
    parser_runserver.set_defaults(func=runserver)
    parser_runserver.add_argument(
        '--esp', action='store_true', help='Run server for ESP-32 ')

    parser_down = subparsers.add_parser(
        'down', help='Stop all containers')
    parser_down.set_defaults(func=down)

    parser_build_flash_esp = subparsers.add_parser(
        'build-flash-esp', help='Build and flash firmware to esp32')
    parser_build_flash_esp.set_defaults(func=build_flash_esp)


    parser_shell = subparsers.add_parser(
        'shell', help='Run shell in container')
    parser_shell.set_defaults(func=shell)

    parser_shell.add_argument(
        'container', choices=['firmware', 'controller', 'backend', 'frontend', 'unity_webgl_server'], help='Container to run shell in')
    
    

    

    parsed_args, remaining_args = parser.parse_known_args()
    command_map = {
        'buildf': build_firmware,
        'build': build,
        'build-esp': build_esp,
        'format': format_code,
        'lint': lint,
        'test': test,
        'test-esp': test_esp,
        'gdb': gdb,
        'runserver': runserver,
        'down': down,
        'build-flash-esp': build_flash_esp,
        'shell': shell
    }

    # Call the function for the first command
    command_map[parsed_args.command](**vars(parsed_args))

    # Loop through the remaining arguments and call corresponding functions
    while remaining_args:
        next_command = remaining_args.pop(0)
        if next_command in command_map:
            args_for_command = vars(
                subparsers.choices[next_command].parse_args(remaining_args))
            command_map[next_command](**args_for_command)
            break
        else:
            print(f"Unknown command: {next_command}")
            exit(1)

    


if __name__ == "__main__":
    main()