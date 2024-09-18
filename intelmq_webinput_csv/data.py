"""
SPDX-FileCopyrightText: 2016, 2017, 2022-2023 Bundesamt für Sicherheit in der Informationstechnik
SPDX-License-Identifier: AGPL-3.0-or-later
Software engineering by Intevation GmbH <https://intevation.de>
"""
from copy import deepcopy

from intelmq.lib.message import Event

"""
Fields left out in this example event are:
destination.geolocation.latitude
destination.geolocation.longitude
event_hash
misp.attribute_uuid
misp.event_uuid
source.geolocation.latitude
source.geolocation.longitude
"""

EXAMPLE_EVENT = {
    "classification.identifier": "Test-identifier",
    "classification.taxonomy": "test",
    "classification.type": "test",
    "comment": "Test Comment",
    "destination.abuse_contact": "abuse@destination.example.com",
    "destination.account": "destination account",
    "destination.allocated": "2023-06-28 10:00:00+00",
    "destination.as_name": "Destination AS",
    "destination.asn": "64496",
    "destination.domain_suffix": "com",
    "destination.fqdn": "destination.example.com",
    "destination.geolocation.cc": "US",
    "destination.geolocation.city": "Example City",
    "destination.geolocation.country": "Untited States of America",
    "destination.geolocation.region": "Example Region",
    "destination.geolocation.state": "Example State",
    "destination.ip": "203.0.113.2",
    "destination.local_hostname": "destination.lan",
    "destination.local_ip": "192.168.0.1",
    "destination.network": "203.0.113.0/24",
    "destination.port": "1682",
    "destination.registry": "ARIN",
    "destination.reverse_dns": "reverse-destination.example.com",
    "destination.tor_node": False,
    "destination.url": "https://destination.example.org/bar",
    "destination.urlpath": "/bar",
    "event_description.target": "Event Description Target",
    "event_description.text": "Event Description Text",
    "event_description.url": "http://event.description.example.net/",
    "extra": {"nothing": "here"},
    "feed.accuracy": "100",
    "feed.code": "Example-feed-code",
    "feed.documentation": "https://feed.example.net/docs",
    "feed.name": "Example feed name",
    "feed.provider": "Example Feed Provider",
    "feed.url": "https://feed.example.net/feed",
    "malware.hash.md5": "68b329da9893e34099c7d8ad5cb9c940",
    "malware.hash.sha1": "adc83b19e793491b1c6ea0fd8b46cd9f32e592fc",
    "malware.hash.sha256": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b",
    "malware.name": "Malware Name",
    "malware.version": "0.1",
    "output": {"data": "just chunk"},
    "protocol.application": "http",
    "protocol.transport": "tcp",
    "raw": "RXhhbXBsZSBEYXRhIG9ubHkK",
    "rtir_id": "1",
    "screenshot_url": "https://example.net/screenshot.png",
    "source.abuse_contact": "abuse@source.example.org",
    "source.account": "source account",
    "source.allocated": "2023-06-28 09:00:00+00",
    "source.as_name": "Source AS",
    "source.asn": "64497",
    "source.domain_suffix": "org",
    "source.fqdn": "source.example.org",
    "source.geolocation.cc": "FR",
    "source.geolocation.city": "ville",
    "source.geolocation.country": "France",
    "source.geolocation.cymru_cc": "FR",
    "source.geolocation.geoip_cc": "FR",
    "source.geolocation.region": "region",
    "source.geolocation.state": "etat",
    "source.ip": "198.18.0.85",
    "source.local_hostname": "source.lan",
    "source.local_ip": "10.0.0.1",
    "source.network": "198.18.0.0/15",
    "source.port": "80",
    "source.registry": "RIPE",
    "source.reverse_dns": "reverse-source.example.org",
    "source.tor_node": False,
    "source.url": "http://source.example.org/foo",
    "source.urlpath": "/foo",
    "status": "online",
    "time.observation": "2023-06-29 09:46:26+00",
    "time.source": "2023-06-29 08:44:22+00",
    "tlp": "GREEN",
}
EXAMPLE_EVENT = Event(EXAMPLE_EVENT)

EXAMPLE_DIRECTIVES = {
    "source_directives": [
        {
            # provide all fields as possible aggregate identifiers
            # only useful for previews/rendering tests
            # a deep copy is required otherwise the json dump called by psycopg2 detects a circular reference
            "aggregate_identifier": deepcopy(EXAMPLE_EVENT),
            "event_data_format": "webinput_fallback_csv_inline",
            "medium": "email",
            "notification_format": "default",
            "notification_interval": 86400,
            "recipient_address": "provider@localhost",
            "template_name": "webinput_fallback_provider"
        }
    ]
}

EXAMPLE_CERTBUND_EVENT = EXAMPLE_EVENT.copy()
EXAMPLE_CERTBUND_EVENT.add('extra.certbund', EXAMPLE_DIRECTIVES)
