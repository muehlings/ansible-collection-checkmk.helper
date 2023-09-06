#!/usr/bin/env python3

# Usage: ./get_hosts.py > /etc/ansible/[host|group]_vars/hosts.yaml
# Get this file: git clone https://github.com/muehlings/ansible-checkmk.helpers

"""
# Example output:
>>> 
---
users:
- auth_option:
    auth_type: password
    password: GENERATED_PASSWORD 
  contact_options:
    fallback_contact: false
  customer: provider
  disable_login: false
  fullname: cmkuser
  interface_options:
    interface_theme: default
    sidebar_position: left
  name: cmkadmin
  roles:
  - user
  state: present
  title: CMK monitoring user 
"""

# related documentation:
# https://pyyaml.org/wiki/PyYAMLDocumentation
# https://docs.python.org/3/library/dataclasses.html
# https://docs.checkmk.com/latest/en/rest_api.html

import pprint
import requests
import yaml
import json
import string
import secrets
from dataclasses import dataclass
from config import USERNAME, PASSWORD, HOST_NAME, SITE_NAME

# when we get entries with "*/collections/all" which we can't change or should not modify,
# add them manually to the BLACKLIST (different entry points require different BLACKLIST)
BLACKLIST = ['agent', 'address_family', 'snmp_ds', 'piggyback', 'automation', 'cmkadmin']
HOST_NAME = HOST_NAME
SITE_NAME = SITE_NAME
USERNAME = USERNAME
PASSWORD = PASSWORD
API_URL = f"https://{HOST_NAME}/{SITE_NAME}/check_mk/api/1.0"
ALL_ENDPOINT = f"{API_URL}/domain-types/user_config/collections/all"
ITEM_ENDPOINT = f"{API_URL}/objects/user_config/"

session = requests.session()
session.headers['Authorization'] = f"Bearer {USERNAME} {PASSWORD}"
session.headers['Accept'] = 'application/json'

@dataclass
class ShortUser():
    """User for API request"""
    name: str
    title: str
    fullname: str
    customer: str
    disable_login: str
    roles: list
    auth_option: dict
    interface_options: dict
    contact_options: dict
    state: str = "present"

def generate_password():
    alphabet = string.ascii_letters + string.digits + string.punctuation 
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(10))
        if (    any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and all(c not in ['\\', '"', "'", '-', '#', '@', '%', '*', '|', '!', '{', '(', '[', ']', ')', '}', '^', '´', '`', '<', '>', ',', '$', '&', ':'] for c in password)
            and sum(c.isdigit() for c in password) >= 1):
            break
    return password

def get_items():
    resp = session.get(
        ALL_ENDPOINT,
        params={  # goes into query string
        },
    )

    if resp.status_code == 200:
    #    pprint.pprint(resp.json())
        values = resp.json()['value']
        return [ item["id"] for item in values ]
    elif resp.status_code == 204:
        ...
    else:
        raise RuntimeError(pprint.pformat(resp.json()))

def get_item(item):
    resp = session.get(
        ITEM_ENDPOINT + item,
    )
    if resp.status_code == 200:
#        pprint.pprint(resp.json())
        item = resp.json()
        name = item['id']
        title = item['title']
        fullname = item['extensions'].pop('fullname')
        customer = item['extensions']['customer']
        disable_login =  item['extensions']['disable_login']
        roles =  item['extensions']['roles']
        auth_option = {'auth_type': 'password', 'password': generate_password()}
        interface_options =  item['extensions']['interface_options']
        contact_options = item['extensions'].get('contact_options', {'fallback_contact': False})
        itemRequest = ShortUser(name, title, fullname, customer, disable_login, roles, auth_option, interface_options, contact_options)
        if not name in BLACKLIST:
            return itemRequest.__dict__
    elif resp.status_code == 204: 
        print("Done")
    else:
        raise RuntimeError(pprint.pformat(resp.json()))

users = []
for item in get_items():
    user = get_item(item)
    if user != None:
        users.append(user)
with open('vars/users.yaml', 'w') as yaml_file:
    print(yaml.dump({'users': users}, default_flow_style=False, indent=2, allow_unicode=True, explicit_start=True), file=yaml_file)
