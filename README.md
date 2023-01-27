# Python Password Changer
Python password changer for multiple hosts via ssh (paramiko_expect).

# Configuration
Edit **config_pass.yml**:
```
config:
  username: myname
  hostsfile: hosts.txt
  oldpsw: test
  newpsw: test2
  invert-psw: False
```

- **username** username to connect to ssh server
- **hostsfile** list of hosts, 1 per line
- **oldpsw** current password for all hosts
- **newpsw** new password you want to set for all hosts
- **invert_psw** True|False if you want to use the oldpsw as the new password and newpsw as the old password
