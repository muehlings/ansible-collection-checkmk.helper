#!/usr/bin/env python3

# Usage: ./get_folders.py > /etc/ansible/[host|group]_vars/folders.yaml
# Get this file: git clone https://github.com/muehlings/ansible-checkmk.helpers

"""
# Example output:
>>> 
---
folders:
- attributes:
    tag_agent: special-agents
  name: special-agent
  path: /special-agent
- attributes:
    tag_agent: no-agent
    tag_snmp_ds: snmp-v2
  name: snmp
  path: /snmp
- attributes:
    tag_agent: no-agent
  name: piggyback
  path: /piggyback
- attributes:
    tag_agent: cmk-agent
  name: cmk-agent
  path: /cmk-agent
"""

# related documentation:
# https://pyyaml.org/wiki/PyYAMLDocumentation
# https://docs.python.org/3/library/dataclasses.html
# https://docs.checkmk.com/latest/en/rest_api.html

import pprint
import requests
import yaml
import json
from dataclasses import dataclass
from config import USERNAME, PASSWORD, HOST_NAME, SITE_NAME

# when we get entries with "*/collections/all" which we can't change or should not modify,
# add them manually to the BLACKLIST (different entry points require different BLACKLIST)
BLACKLIST = ['agent', 'address_family', 'snmp_ds', 'automation', 'cmkadmin']
HOST_NAME = HOST_NAME
SITE_NAME = SITE_NAME
USERNAME = USERNAME
PASSWORD = PASSWORD
API_URL = f"https://{HOST_NAME}/{SITE_NAME}/check_mk/api/1.0"
ALL_ENDPOINT = f"{API_URL}/domain-types/folder_config/collections/all"
ITEM_ENDPOINT = f"{API_URL}/objects/folder_config/"

session = requests.session()
session.headers['Authorization'] = f"Bearer {USERNAME} {PASSWORD}"
session.headers['Accept'] = 'application/json'

@dataclass
class ShortFolder():
    """folder payload for API request"""
    name: str
    path: str
    attributes: dict

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
        name = item['title']
        path = item['extensions']['path']
        attributes = item['extensions']['attributes']
        attributes.pop('meta_data')

        if name in BLACKLIST:
            return 
        itemRequest = ShortFolder(name, path, attributes) 
        return itemRequest.__dict__
    elif resp.status_code == 204: 
        print("Done")
    else:
        raise RuntimeError(pprint.pformat(resp.json()))

folders = []
for item in get_items():
    folder = get_item(item)
    if folder != None:
        folders.append(folder)
with open('vars/folders.yaml', 'w') as yaml_file:
    print(yaml.dump({'folders': folders}, default_flow_style=False, indent=2, allow_unicode=True, explicit_start=True), file=yaml_file)
