#!/usr/bin/env python
from subprocess import call

STARTUP_SCRIPT = '/etc/rc.local'
RUN_MONITOR = 'sudo -i screen -d -m -S monitor python /opt/bitfury/chainmonitor/run.py'

with open(STARTUP_SCRIPT, 'r') as fp:
    lines = fp.read().split('\n')

for index, line in enumerate(lines[:]):
    if '/chainmonitor/run' in line:
        lines[index] = RUN_MONITOR
        break
    if line.startswith('exit'):
        lines.insert(index, RUN_MONITOR + '\n')
        break

if RUN_MONITOR not in lines:
    lines.append(RUN_MONITOR)

with open(STARTUP_SCRIPT, 'w') as fp:
    fp.write('\n'.join(lines))

call('screen -S monitor -X quit', shell=True)
call(RUN_MONITOR, shell=True)
