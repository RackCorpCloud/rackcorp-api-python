import logging
import os
import sys
import time

from . import client, dns

logger = logging.getLogger(__name__)


def _prepare_new_record() -> dns.DnsRecord:
    """
    Prepare a new DNS record for the Rackcorp API.
    """
    domain = os.environ.get("CERTBOT_DOMAIN")
    if not domain:
        return None
    validation = os.environ.get("CERTBOT_VALIDATION")

    record_name = domain.split(".")[0]
    zone_name = domain[len(record_name) + 1 :]

    new_record = dns.DnsRecord(
        lookup=f"_acme-challenge.{record_name}",
        type=dns.DnsRecordType.TXT,
        data=validation,
        ttl=120,
        domain_name=zone_name,
    )

    return new_record


def _find_domain_id(client: client.Client, record: dns.DnsDomain) -> str:
    domains = client.dns.domain_getall()
    for d in domains:
        if d.name == record.domain_name:
            return d.id
    return None


def _find_record_id(client: client.Client, record: dns.DnsDomain) -> str:
    """
    Find the record ID for an existing DNS record.
    """
    dom = client.dns.domain_get(record.domain_id)
    for r in dom.records:
        if r.lookup == record.lookup and r.type == record.type:
            return r.id
    return None


class CertbotAuthHook:
    def main(self) -> int:
        """
        Main entry point for the Certbot Auth Hook.
        """
        new_record = _prepare_new_record()
        if not new_record:
            logger.error("CERTBOT_DOMAIN and CERTBOT_VALIDATION must be provided.")
            return 1

        self.client = client.Client()

        domain_id = _find_domain_id(self.client, new_record)
        if not domain_id:
            logger.error(f"Zone '{new_record.domain_name}' not found.")
            return 1
        new_record.domain_id = domain_id

        record_id = _find_record_id(self.client, new_record)

        if record_id:
            logger.info(
                f"Updating existing record {new_record.lookup}.{new_record.domain_name}"
            )
            new_record.id = record_id
            self.client.dns.record_update(new_record)
        else:
            logger.info(f"Creating record {new_record.lookup}.{new_record.domain_name}")
            self.client.dns.record_create(new_record)

        logger.info("Pausing to allow for DNS propagation")
        time.sleep(10)
        return 0


class CertbotCleanupHook:
    def main(self):
        """
        Main entry point for the Certbot Cleanup Hook.
        """
        new_record = _prepare_new_record()
        if not new_record:
            logger.error("CERTBOT_DOMAIN and CERTBOT_VALIDATION must be provided.")
            return 1

        self.client = client.Client()

        domain_id = _find_domain_id(self.client, new_record)
        if not domain_id:
            logger.error(f"Zone '{new_record.domain_name}' not found.")
            return 1
        new_record.domain_id = domain_id

        record_id = _find_record_id(self.client, new_record)
        if record_id:
            logger.info(
                f"Deleting existing record {new_record.lookup}.{new_record.domain_name}"
            )
            self.client.dns.record_delete(record_id)

        return 0


if len(sys.argv) > 1:
    logging.basicConfig(level=logging.DEBUG)
    if sys.argv[1] == "CertbotAuthHook":
        sys.exit(CertbotAuthHook().main())
    elif sys.argv[1] == "CertbotCleanupHook":
        sys.exit(CertbotCleanupHook().main())
    else:
        logger.error(f"Unknown command: {sys.argv[1]}")
        sys.exit(1)
