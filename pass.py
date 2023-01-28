#!/usr/bin/env python3

from __future__ import print_function

import argparse
import getpass
import os
import re
import traceback
import warnings
import paramiko
import yaml
from colorama import init, Fore
from paramiko_expect import SSHClientInteraction
from prettytable import PrettyTable, PLAIN_COLUMNS

class HostStatus:
    init()

    def __init__(self, hostname, status, testconn):
        self.hostname = hostname
        self.status = status
        self.testconn = testconn

    def return_status(self):
        end = Fore.WHITE
        if self.status:
            color = Fore.GREEN
            if self.testconn:
                status = 'ok'
            else:
                status = 'changed'
        else:
            color = Fore.RED
            status = 'failed'

        ret = (color + self.hostname + end, color + status + end)
        return ret

    def print_status(self):
        stat = self.return_status()
        print(stat[0] + ' ' + stat[1])


class Host():
    CONST_PROMPT = r'.*[ ~][\$\#]\s*'
    CONST_OLDPWPROMPT = r'.*(password)\s*\:\s*'
    CONST_NEWPWPROMPT = r'.*(password)\s*\:\s*'
    CONST_NEWPWPROMPT2 = r'.*(password)\s*\:\s*'
    CONST_SUCCESSMSG = r'.*passwd\:.*(successfully).*'
    updated = []

    warnings.filterwarnings("ignore", module='.*paramiko')

    def __init__(self, hostname, username, oldpsw, newpsw):
        self.hostname = hostname
        self.username = username
        self.oldpsw = oldpsw
        self.newpsw = newpsw
        self.changed = False
        self.log = []
        self.proxy = None
        ssh_config_file = os.path.expanduser('~/.ssh/config')
        if os.path.isfile(ssh_config_file):
            config = paramiko.SSHConfig()
            with open(ssh_config_file) as config_file:
                config.parse(config_file)
            host_config = config.lookup(hostname)
            if 'proxycommand' in host_config:
                self.proxy = host_config['proxycommand']

    def log_msg(self, message):
        self.log.append(message)

    def test_connection(self, verbose):
        try:
            if verbose:
                print(f"connecting to {self.hostname}...")
            # Create a new SSH client object
            client = paramiko.SSHClient()

            # Set SSH key parameters to auto accept unknown hosts
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the host
            proxy = None
            if self.proxy is not None:
                proxy = paramiko.ProxyCommand(self.proxy)
            client.connect(hostname=self.hostname, timeout=20, sock=proxy,
                           username=self.username, password=self.oldpsw)

            output=""
            command = "hostname"
            stdin, stdout, stderr = client.exec_command(command)
            if verbose:
                print("succuessfully connected")
                stdout=stdout.readlines()
                print(command)
                for line in stdout:
                    if line != "": 
                        output=output+line.rstrip()
                if output != "":
                    print(output)
                else:
                    print("There was no output for this command")
                print("connection closed")
            self.changed = True
            client.close()

        except Exception:
            self.log_msg(traceback.format_exc())
        finally:
            try:
                client.close()
            except Exception:
                pass
        status = HostStatus(self.hostname, self.changed, True)
        Host.updated.append(status)
        if verbose:
            status.print_status()
            if not self.changed:
                print(self.log)
            print("--------------------------------------------------------------------")

    def change_psw(self, verbose):
        try:
            if verbose:
                print(f"connecting to {self.hostname}...")
            # Create a new SSH client object
            client = paramiko.SSHClient()

            # Set SSH key parameters to auto accept unknown hosts
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the host
            proxy = None
            if self.proxy is not None:
                proxy = paramiko.ProxyCommand(self.proxy)
            client.connect(hostname=self.hostname, timeout=20, sock=proxy,
                           username=self.username, password=self.oldpsw)

            if verbose:
                print(f"connected to {self.hostname}")

            with SSHClientInteraction(
                    client, timeout=10, display=False,
                    output_callback=lambda m: self.log_msg(m)) \
                    as interact:
                found_index = interact.expect(
                    [Host.CONST_PROMPT, Host.CONST_OLDPWPROMPT])
                if found_index == 0:
                    interact.send("passwd")
                    interact.expect(Host.CONST_OLDPWPROMPT)
                
                interact.send(self.oldpsw)
                interact.expect(Host.CONST_NEWPWPROMPT)
                interact.send(self.newpsw)
                interact.expect(Host.CONST_NEWPWPROMPT2)
                interact.send(self.newpsw)

                if found_index == 0:
                    interact.expect(Host.CONST_SUCCESSMSG)
                    interact.send('exit')
                interact.expect()
                self.changed = True
                client.close()

        except Exception:
            self.log_msg(traceback.format_exc())
        finally:
            try:
                client.close()
            except Exception:
                pass
        status = HostStatus(self.hostname, self.changed, False)
        Host.updated.append(status)
        if verbose:
            status.print_status()
            if not self.changed:
                print(self.log)

class Config():
    def __init__(self, cfgfile='config_pass.yml'):
        with open(cfgfile, 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)['config']
            self.username = cfg['username']
            self.oldpsw = cfg['oldpsw']
            self.newpsw = cfg['newpsw']
            invert_psw = cfg['invert_psw']
        
        if invert_psw:
            aux_psw = newpsw
            newpsw = oldpsw
            oldpsw = aux_psw

    def get_hosts(self):
        ret = []
        with open("hosts.txt") as file:
            for host in file:
                ret.append(Host(host.rstrip(), self.username, self.oldpsw, self.newpsw))

        return ret

def main():
    parser = argparse.ArgumentParser(description='Changes password on multiple hosts.')
    parser.add_argument('-f', '--file', nargs=1, help='Path to file with configuration.')
    parser.add_argument('-v', '--verbose', action='store_const', const=True, help='Verbose output.')
    parser.add_argument('-t', '--testconn', action='store_const', const=True, help='Test connection to host')
    parser.add_argument('-e', '--export', action='store_const', const=True, help='Export report of successul and failed hosts')
    args = parser.parse_args()
    cfgfilename = 'config_pass.yml'
    if args.file:
        cfgfilename = args.file[0]

    verbose = False
    if args.verbose:
        verbose = True

    config = Config(cfgfile=cfgfilename)
    for host in config.get_hosts():
        if args.testconn:
            host.test_connection(verbose)
        else:
            host.change_psw(verbose)

    table = PrettyTable()
    table.field_names = ["hostname", "status"]
    table.set_style(PLAIN_COLUMNS)
    table.align = "l"

    if args.export:
        with open("hosts_ok.txt", "w") as hosts_ok:
            with open("hosts_fail.txt", "w") as hosts_fail:
                for host in Host.updated:
                    if host.status:
                        hosts_ok.write(host.hostname + '\n')
                    else:
                        hosts_fail.write(host.hostname + '\n')

    for host in Host.updated:
        table.add_row(host.return_status())

    print(table)

if __name__ == '__main__':
    main()
