#!/usr/bin/env python3

# Usage: ./get_hosts.py > /etc/ansible/[host|group]_vars/hosts.yaml
# Get this file: git clone https://github.com/muehlings/ansible-checkmk.helpers

"""
# Example output:
>>> 
---
tag_groups:
- choices:
  - aux_tags: []
    id: prod
    title: Productive system
  - aux_tags: []
    id: critical
    title: Business critical
  - aux_tags: []
    id: test
    title: Test system
  - aux_tags: []
    id: offline
    title: Do not monitor this host
  ident: criticality
  title: Criticality
  topic: Tags
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
BLACKLIST = ['agent', 'address_family', 'snmp_ds', 'piggyback', 'automation', 'cmkadmin']
HOST_NAME = HOST_NAME
SITE_NAME = SITE_NAME
USERNAME = USERNAME
PASSWORD = PASSWORD
API_URL = f"https://{HOST_NAME}/{SITE_NAME}/check_mk/api/1.0"
ALL_ENDPOINT = f"{API_URL}/domain-types/host_tag_group/collections/all"
ITEM_ENDPOINT = f"{API_URL}/objects/host_tag_group/"

session = requests.session()
session.headers['Authorization'] = f"Bearer {USERNAME} {PASSWORD}"
session.headers['Accept'] = 'application/json'

@dataclass
class ShortTag_Group():
    """tag_group payload for API request"""
    ident: str
    choices: dict
    title: str
    topic: str

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
        ident = item['id']
        title = item['title']
        topic = item['extensions'].pop('topic')
        choices = item['extensions']['tags']
        if ident in BLACKLIST:
            return 
        itemRequest = ShortTag_Group(ident, choices, title, topic) 
        return itemRequest.__dict__
    elif resp.status_code == 204: 
        print("Done")
    else:
        raise RuntimeError(pprint.pformat(resp.json()))

tag_groups = []
for item in get_items():
    tag_group = get_item(item)
    if tag_group != None:
        tag_groups.append(tag_group)
with open('vars/tag_groups.yaml', 'w') as yaml_file:
    print(yaml.dump({'tag_groups': tag_groups}, default_flow_style=False, indent=2, allow_unicode=True, explicit_start=True), file=yaml_file)
