<h1> python-mailing-list </h1>
A (very) simple mailing-list forwarder for Python

This is a single-file python script that is designed to plug into a mail pipeline like *procmail* or such.
You would typically configure a specific address for the mailing list (list@domain.com), and create a _.procmailrc_
in that user's home dir to call the script, e.g.:

:0
| /usr/bin/python3 mailing-list.py

It uses three configuration files per mailing list:
- An _allowed users_ file
- A _list name_ file
- A _recipients_ file
