# pass.py
Python password changer for multiple hosts via ssh (paramiko_expect) by reading a KeePass2 database file.

# configuration
Edit **config_pass.yml**:
```
keepass:
  dbfile: Database.kdbx
  oldentry: test
  newentry: test2
  group: home
  invert-psw: False
```

- **dbfile** is the name of the KeePass2 database file
- **oldentry** is the name of the entry in KeePass that is going to be read
    In this entry you need to have:
    - **User Name**: user whose password will be modified
    - **Password:** current password
    - **URL:** list of hosts separated by a space
- **newentry** is the name of the entry in KeePass where the result is going to be written
    In this entry you need to have:
    - **User Name:** user whose password will be modified
    - **Password:** new password
- **group** is the group name to use in the KeePass database file
- **invert-psw** True|False if you want to use the oldentry:password as the new password and newentry:password as the old password

# about
Not originally coded by me. 
Couln't find who the creator is, if you know please let me know.
