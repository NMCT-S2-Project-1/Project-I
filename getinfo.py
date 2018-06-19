
import base64
import grp
import json
import logging
import os
import re
import shlex
import subprocess
import sys
from getpass import getpass, getuser
from ipaddress import IPv4Interface, IPv6Interface


API_URL = 'https://'
LOCALHOST = IPv4Interface('127.0.0.1/32')
NAME = 'Project-I'
re_email = re.compile(r'[a-z\-]+\.[a-z\-]+(\.[a-z]+)*\d*@(student\.)?howest\.be')

re_ether = re.compile(r'^(?P<num>\d+): (?P<name>[^:]+):.*?ether (?P<mac>([0-9a-f]{2}:?){6}).*$')
re_ipv4 = re.compile(
    r'^(?P<num>\d+):\s*(?P<name>\w+\d+[\w\d]*)\s+inet (?P<ipv4>(\d{1,3}\.?){4}/\d{1,2}) brd \S+ scope (?P<scope>\w+).*$')
re_ipv6 = re.compile(r'^(?P<num>\d+):\s*(?P<name>\w+\d+[\w\d]*)\s+inet6 (?P<ipv6>\S+) scope (?P<scope>\w+).*$')
venv_regex = re.compile(r'^(?P<venv>(\/\w+){2,}\/v?env)\/bin\/python3?$')

MODE_TEST = False
MODE_DEV = True

LINE = '-' * 80
DOUBLELINE = '=' * 80
log = logging.getLogger(__name__)


def error(*args, **kwargs):
    print("ERROR: ", *args, **kwargs)


def cmd_exec(cmd, split=False, **kwargs):
    cmd = shlex.split(cmd) if split else cmd
    kwargs.setdefault('shell', True)
    return subprocess.run(cmd, **kwargs)


def cmd_output(cmd, **kwargs):
    kwargs['stdout'] = subprocess.PIPE
    return cmd_exec(cmd, **kwargs).stdout.decode().strip()


def cmd_retval(cmd, **kwargs):
    return cmd_exec(cmd, **kwargs).returncode


def cmd_returns(cmd, retval, **kwargs):
    return cmd_retval(cmd, **kwargs) == retval


def cmd_success(cmd, **kwargs):
    return cmd_returns(cmd, 0, **kwargs)


def cmd_match(cmd, regexp, flags=None, **kwargs):
    flags = (flags or getattr(regexp, 'flag', 0)) | re.MULTILINE
    regexp = re.compile(getattr(regexp, 'pattern', regexp), flags)
    return [match.groupdict() for match in
            regexp.finditer(cmd_output(cmd, **kwargs))]


def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def get_networks():
    ifaces = {
        line['name']: {
            'mac': line['mac'].replace(':', '-'),
            'ipv4': [],
            'ipv6': [],
        } for line in cmd_match('/sbin/ip -o l', re_ether)
    }
    if_names = list(ifaces.keys())
    log.info("Found {} network interfaces: {}".format(len(if_names), if_names))
    for match in cmd_match(
            '/sbin/ip -o a s',
            re_ipv4):
        iface = match.get('name')
        ipaddr = match.get('ipv4')
        ifaces[iface]['ipv4'].append(IPv4Interface(ipaddr).exploded)
        log.info("Found IPv4 on {} on interface {}".format(ipaddr, iface))
    for match in cmd_match(
            '/sbin/ip -o a s',
            re_ipv6):
        iface = match.get('name')
        ipaddr = match.get('ipv6')
        ifaces[iface]['ipv6'].append(IPv6Interface(ipaddr).exploded)
        log.info("Found IPv6on {} on interface {}".format(ipaddr, iface))
    return ifaces


def get_system_properties():
    status = None
    host = cmd_output('/bin/hostname')
    boot_ip = cmd_match('cat /boot/cmdline.txt 2>/dev/null', re.compile('ip=(?P<ip>\w+)'))
    status = True
    globals().update(locals())
    return locals()


def get_python():
    status = None
    interpreter = sys.executable
    version = list(sys.version_info)
    virtual_env = os.environ.get('VIRTUAL_ENV') or venv_regex.search(interpreter).group('venv') \
        if venv_regex.search(interpreter) else None
    if not virtual_env or sys.version_info.major < 3:
        status = False
    else:
        if sys.version_info.minor < 5:
            log.warning("Python release < 3.5.0")
            status = "Outdated minor version"
        else:
            status = True
    globals().update(locals())
    return locals()


def get_os_credentials():
    status = None
    print('Enter login credentials for the RPi (SSH):')

    while True:
        user = input("{} login [{}]: ".format(cmd_output('/bin/hostname'), getuser())) or getuser()
        if not user:
            print('Username cannot be blank!')
            continue
        passwd = getpass("{}@{}'s password:: ".format(user, cmd_output('/bin/hostname')))
        if not passwd:
            print('Password cannot be blank')
            continue
        if user not in grp.getgrnam('sudo').gr_mem:
            print("Sudo check failed! ")
        print('Recorded: {}:{}'.format(user, passwd))
        if (input('Is this information correct? [y/n] ').lower()) == 'y':
            break
        print("OK, try again...")
    passwd = encode(user, passwd)
    groups = list(cmd_output('/usr/bin/groups').split(" ")),
    log.info("Group memberships: {}".format(groups))
    globals().update(locals())
    return locals()


def get_app_credentials():
    print('Enter credentials for the application (website):')
    credentials = []
    done = False
    while not done:
        user = input('Username: ')
        if not user:
            print('Username cannot be blank')
            continue

        passwd = input('Password: ')
        if not passwd:
            print('Password cannot be blank')
            continue
        comment = input('Extra info (optional): ')
        cred = {'user': user, 'passwd': passwd, 'comment': comment}
        print('Recorded: \n{}'.format(cred))
        ok = (input('Is this information correct? [Y/n] ').lower() or 'y') == 'y'
        if not ok:
            continue
        cred['passwd'] = encode(cred['user'], cred['passwd'])
        credentials.append(cred)
        done = (input('Do you want to add another credential? [y/N] ').lower() or 'n') == 'n'
    print('Recorded {} application credentials'.format(len(credentials)))
    return credentials


def save_to_file(data, file='about.yml', mode='a'):
    try:
        with open(file, mode) as f:
            json.dump(data, f, indent=4)
        print('{} data to {}'.format('Appended' if mode == 'a' else 'Wrote', file))
        return True
    except Exception as e:
        log.error("Failed to write data to {}: {}".format(file, e))
        return False


def output_results(data):
    print('\n\n', LINE, 'Output data', LINE, json.dumps(data), LINE, sep='\n')
    ok = save_to_file(data, 'info.json', 'w')


def main():
    failed = False
    creds = {}
    data = {'credentials': creds}
    print(DOUBLELINE, "Raspi-check & indientool".format(name=NAME), DOUBLELINE, sep='\n')

    data['system'] = get_system_properties()
    creds['system'] = get_os_credentials()

    data['python'] = get_python()

    data['network'] = get_networks()

    creds['application'] = get_app_credentials()
    output_results(data)
    return -2 if failed else 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='sysinfo.log')
    result = main()
    exit(result)
