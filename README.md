Installation
============
First, prepare for mass installation:
Unzip chainmonitor.zip and edit chainmonitor/config.py to point to your email server.
Run "python test_mail.py" to verify that your email settings are correct.

Now, copy the configured chainmonitor folder to all miners.
On each miner, the chainmonitor folder has to be copied to /opt/bitfury.

On each miner run the following:
* cd /opt/bitfury/chainmonitor
* python install.py

You're done.
