<h1> python-mailing-list </h1>
A (very) simple mailing-list forwarder for Python

This is a single-file python script that is designed to plug into a mail pipeline like *procmail* or such.
You would typically configure a specific address for the mailing list (like `mylist@domain.com`), and create a _.procmailrc_
in that user's home dir to call the script, e.g.:
<pre>
:0
| /usr/bin/python3 mailing-list.py mylist@domain.com /path/to/listdir
</pre>

The first two parameters are required: the listname (the full email address of the list), and the directory where the list files reside.

It uses three configuration files per mailing list, found in the dir pointed to by the second arg:
- An _allowed users_ file
- A _list name_ file
- A _recipients_ file

The configuration files start with the mailing list address (without domain).  So if the list name is "mylist" the files would be:
- mylist.senders
- mylist.recipients
- mylist.listname

The _.senders_ and _.recipients_ files contain just a list of email addresses, one per line.  The email addresses are parsed with python's `email.utils.parseaddr()` function, so they can be like `Real Name <real.name@domain.com>` or `<real.name@domain.com>` or just `real.name@domain.com`.

The _.listname_ file contains two lines:
The first line is the name of the mailing list, which is prepended to the Subject line with brackets.
The second line is the email address of an administrator, which is used for bounces (for incoming addresses that aren't in the _mylist.senders_ file).

The simplistic nature of this engine is to make it easy to import a list from an outside source, like a database of users, and make it available as a conventional "announcement" list.

The reply address of the list is the sender.

A "discussion"-type list is done by simply having the same email addresses in both _.senders_ and _.recipients_; i.e., anyone on the list can send an email to the entire list.

Some filtering is performed to attempt to minimize duplicate messages.  For example, if the list address is Cc'd (as might happen if someone does a "reply all" to a message), then the person getting the reply should only receive one message, not two.
