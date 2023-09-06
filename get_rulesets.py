#!/usr/bin/env python3

# Usage: ./get_hosts.py > /etc/ansible/[host|group]_vars/hosts.yaml
# Get this file: git clone https://github.com/muehlings/ansible-checkmk.helpers

"""
# Example output:
>>> 
---
rulesets:
- - rule:
      conditions:
        host_labels: []
        host_tags: []
        service_labels: []
      location:
        folder: /piggyback
      properties:
        comment: 'piggyback'
        description: Assignment of hosts to host groups - Do not monitor
      value_raw: '''Do_not_monitor'''
    ruleset: host_groups
  - rule:
      conditions:
        host_labels: []
        host_tags:
        - key: criticality
          operator: is
          value: offline
        service_labels: []
      location:
        folder: /
      properties:
        description: Assignment of hosts to host groups - Do not monitor
      value_raw: '''Do_not_monitor'''
    ruleset: host_groups
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
ALL_ENDPOINT = f"{API_URL}/domain-types/ruleset/collections/all"
ITEM_ENDPOINT = f"{API_URL}/domain-types/rule/collections/all" 

session = requests.session()
session.headers['Authorization'] = f"Bearer {USERNAME} {PASSWORD}"
session.headers['Accept'] = 'application/json'

@dataclass
class ShortRule():
    """rule payload for API request"""
    ruleset: str
    rule: dict

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
        ITEM_ENDPOINT,
        params={  # goes into query string
            "ruleset_name": item,  # (required) The name of the ruleset.
        },

    )
    if resp.status_code == 200:
#        pprint.pprint(resp.json())
        rules = resp.json()['value']
        for rule in rules:
            ruleset = rule['extensions']['ruleset']
            folder = rule['extensions']['folder']
            properties = rule['extensions']['properties']
            value_raw = rule['extensions']['value_raw']
            conditions = rule['extensions']['conditions']
            ruleRequest = ShortRule(ruleset, {'properties': properties, 'value_raw': value_raw, 'conditions': conditions, 'location': {'folder': folder}})
            yield ruleRequest.__dict__
    elif resp.status_code == 204: 
        print("Done")
    else:
        raise RuntimeError(pprint.pformat(resp.json()))

rulesets = []
for item in get_items():
    ruleset = get_item(item)
    if ruleset != None:
        rulesets.append(list(ruleset))  # list(ruleset) to unpack generator object from yield in get_item()
with open('vars/rulesets.yaml', 'w') as yaml_file:
    print(yaml.dump({'rulesets': rulesets}, default_flow_style=False, indent=2, allow_unicode=True, explicit_start=True), file=yaml_file)
