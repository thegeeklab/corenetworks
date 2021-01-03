---
title: Setup
---

<!-- prettier-ignore-start -->
<!-- spellchecker-disable -->
{{< toc >}}
<!-- spellchecker-enable -->
<!-- prettier-ignore-end -->

## Installation

<!-- prettier-ignore-start -->
<!-- spellchecker-disable -->
{{< highlight Python "linenos=table" >}}
pip install corenetworks
{{< /highlight >}}
<!-- spellchecker-enable -->
<!-- prettier-ignore-end -->

## Example usage

<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<!-- spellchecker-disable -->
{{< highlight Python "linenos=table" >}}
#!/usr/bin/env python

import requests

from corenetworks import CoreNetworks
from corenetworks.exceptions import CoreNetworksException

try:
    user = "my_user"
    password = "my_password"
    dns = CoreNetworks(user, password, auto_commit=True)

    zones = dns.zones()
    print(zones)
    # [{'name': 'example.com', 'type': 'master'}, {'name': 'test.com', 'type': 'master'}]

    zone = dns.zone(zone="example.com")
    print(zone)
    # [{'active': True, 'dnssec': True, 'master': None, 'name': 'example.com', 'tsig': None, 'type': 'master'}]

    records = dns.records(zone="example.com")
    print(records)
    # [
    #     {'name': '@', 'ttl': '1800', 'type': 'SOA', 'data': 'ns1.core-networks.de. [...]'},
    #     {'name': 'test', 'ttl': '60', 'type': 'A', 'data': '1.2.3.4'},
    #     {'name': '@', 'ttl': '86400', 'type': 'NS', 'data': 'ns1.core-networks.de.'},
    #     {'name': '@', 'ttl': '86400', 'type': 'NS', 'data': 'ns2.core-networks.eu.'},
    #     {'name': '@', 'ttl': '86400', 'type': 'NS', 'data': 'ns3.core-networks.com.'}
    # ]

    filtered = dns.records(zone="example.com", params={"type": ["A", "AAAA"]})
    print(filtered)
    # [{'name': 'test', 'ttl': '3600', 'type': 'A', 'data': '1.2.3.4'}]

    add_record = dns.add_record(
        zone="example.com", params={
            "name": "test",
            "type": "A",
            "data": "127.0.0.1",
            "ttl": 3600,
        }
    )
    print(add_record)
    # [{'name': 'test', 'ttl': '3600', 'type': 'A', 'data': '127.0.0.1'}]

    del_record = dns.delete_record(zone="example.com", params={
        "name": "test",
        "type": "A",
    })
    print(del_record)
    # []

except Exception as e:
    print(str(e))
{{< /highlight >}}
<!-- spellchecker-enable -->
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
