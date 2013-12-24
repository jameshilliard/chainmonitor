#!/usr/bin/env python
from datetime import datetime
from envelopes import Envelope
from subprocess import call
from time import sleep, time
import config
import json
import os
import socket

REBOOTED_FILE = '/var/log/chainmonitor_rebooted'
LOG_FILE = '/var/log/chainmonitor.log'
STATS_FILE = '/run/shm/stat.json'

START_TIME = time()

from_reboot = os.path.exists(REBOOTED_FILE)
if from_reboot:
    os.remove(REBOOTED_FILE)


def truncate_log_file():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 1024 * 1024:
        with open(LOG_FILE, 'r') as fp:
            lines = fp.readlines()
        with open(LOG_FILE, 'w') as fp:
            fp.writelines(lines[-100:])

def log_error(message):
    truncate_log_file()
    log = '%s: %s' % (datetime.now().isoformat(' ').split('.')[0], message)
    print(log)
    with open(LOG_FILE, 'a') as fp:
        fp.write(log + '\n')

last_mail_time = 0

def send_mail(subject, body):
    global last_mail_time

    if time() - last_mail_time < 5 * 60:
        return

    envelope = Envelope(from_addr=config.SENDER_EMAIL, to_addr=config.RECEIVER_EMAIL,
            subject=subject, text_body=body)
    envelope.send(config.SMTP_SERVER, tls=config.SMTP_USE_TLS, port=config.SMTP_PORT,
                  login=config.SMTP_USER, password=config.SMTP_PASSWORD)

    last_mail_time = time()

def get_my_ip():
    for host in ('www.google.com', 'gmail.com', 'heise.de', 'baidu.com',
                 'qq.com', 'sina.com.cn'):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("gmail.com",80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            pass
    return '<unknown>'

def get_stats():
    for i in range(3):
        try:
            with open(STATS_FILE, 'r') as fp:
                return fp.read()
        except:
            sleep(1)

def handle_error(message, body=''):
    if not body:
        body = message
    log_error(message + (body and '\n' + body))
    if not from_reboot:
        send_mail('auto-rebooting on error: %s' % message,
                  'Detected an error in miner with IP %s.\n%s'
                  'The miner will be rebooted automatically.\n'
                  'If such errors happen too often you might have to reset the miner '
                  'by pulling the plug.\n\n'
                  'Contents of stat file:\n\n%s\n'
                  % (get_my_ip(), body and '\n' + body + '\n\n', get_stats()))
        with open(REBOOTED_FILE, 'w') as fp:
            fp.write('reboot at %s' % datetime.now().isoformat(' '))
        call('reboot', shell=True)
        return

    send_mail('chainminer error: %s' % message,
              'A critical error has reappeared shortly after reboot.\n%s'
              'Try resetting miner with IP %s by pulling the plug.\n\n'
              'Contents of stat file:\n\n%s\n'
              % (body and '\n' + body + '\n\n', get_my_ip(), get_stats()))
    sleep(24 * 60 * 60)

def main():
    global from_reboot

    print('Running chainmonitor...')
    if from_reboot:
        print('Detected reboot. Errors in the next two hours get reported as critical.')
    print('Waiting for chainminer...')

    # Allow chainminer to get started
    try:
        sleep(2 * 60)
    except KeyboardInterrupt:
        print('Fast-start')
        sleep(3)

    print('Beginning monitoring...')

    stat_read_errors = 0

    while True:
        # If we run without any problems for at least two hours we can retry rebooting
        if time() - START_TIME > 2 * 60 * 60:
            from_reboot = False

        try:
            with open(STATS_FILE, 'r') as fp:
                stats = json.loads(fp.read())['stats']
        except Exception as e:
            stat_read_errors += 1
            log_error("Couldn't read stats.json: %r. Will retry in one second." % (e,))
            if stat_read_errors > 3:
                handle_error("Can't read %s" % STATS_FILE)
            sleep(1)
            continue

        stat_read_errors = 0

        try:
            reload(config)
            warnings = []
            errors = []
            if time() - os.path.getmtime(STATS_FILE) > 10 * 60:
                errors.append('Stats file not updating - maybe chainminer crashed')
            if stats['hashrate'] < 25 * len(stats['boards']):
                errors.append('Hash rate at merely %s with %d detected boards'
                              % (stats['hashrate'], len(stats['boards'])))
            if stats['good'] < stats['errors']:
                errors.append('Getting too many hashing errors in total')
            for board in stats['boards']:
                if board['good'] < board['spi-errors']:
                    errors.append('Board in slot %s has critical error rate and '
                                  'might be broken: %s good, %s spi-errors'
                                  % (board['slot'], board['good'], board['spi-errors']))
                elif board['good'] < board['errors']:
                    warnings.append('Board in slot %s has very high error rate: '
                                    '%s good, %s errors'
                                    % (board['slot'], board['good'], board['errors']))
            if errors:
                message = errors[0]
                body = ''
                if len(errors) > 1:
                    message = 'Multiple errors'
                    body = '\n'.join(errors + warnings)
                handle_error(message, body)
        except Exception as e:
            handle_error(repr(e))

        sleep(10)

if __name__ == '__main__':
    main()
