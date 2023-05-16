#!/usr/bin/env python3

import argparse
import subprocess
import datetime
from pathlib import Path

def count_failed_attempts():
    with open('/var/log/auth.log', 'r') as f:
        lines = f.readlines()

    failed_attempts = 0
    first_time = None
    last_time = None

    for line in lines:
        if "Failed password" in line or "authentication failure" in line or "Invalid user" in line:
            log_time_str = ' '.join(line.split()[:3])
            log_time = datetime.datetime.strptime(log_time_str, '%b %d %H:%M:%S')

            if first_time is None or log_time < first_time:
                first_time = log_time

            if last_time is None or log_time > last_time:
                last_time = log_time

            failed_attempts += 1

    total_hours = (last_time - first_time).total_seconds() / 3600
    average_attempts_per_hour = failed_attempts / total_hours

    return average_attempts_per_hour

def setup_fail2ban():
    jail_conf = """
    [sshd]
    enabled = true
    port = ssh
    filter = sshd
    logpath = /var/log/auth.log
    maxretry  = 3
    findtime  = 1d
    bantime   = 4w
    ignoreip  = 127.0.0.1
    """
    subprocess.run(['apt-get', 'install', '-y', 'fail2ban'], check=True)
    Path('/etc/fail2ban/jail.local').write_text(jail_conf)
    subprocess.run(['systemctl', 'enable', 'fail2ban'], check=True)
    subprocess.run(['systemctl', 'restart', 'fail2ban'], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup-fail2ban', action='store_true')
    args = parser.parse_args()

    failed_attempts = count_failed_attempts()
    print(f'Failed authentication attempts per hour: {failed_attempts}')

    if failed_attempts > 10:
        print('Warning: More than 10 failed authentication attempts in the last hour.')

        if args.setup_fail2ban:
            confirm = input('Do you want to set up Fail2Ban? (yes/no): ')
            if confirm.lower() == 'yes':
                setup_fail2ban()
                print('Fail2Ban has been set up and started.')
            else:
                print('Aborted Fail2Ban setup.')
        else:
            print('Use --setup-fail2ban option to set up Fail2Ban.')

if __name__ == '__main__':
    main()
