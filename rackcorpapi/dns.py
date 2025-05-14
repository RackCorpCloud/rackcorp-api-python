from . import api, dicthelp
from .strenum import StrEnum
import dataclasses
import enum
import typing


class DnsRecordType(StrEnum):
    A = "A"
    AHASHED = "AHASHED"
    AAAA = "AAAA"
    CAA = "CAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"
    PTR = "PTR"
    TXT = "TXT"
    SRV = "SRV"


@dataclasses.dataclass
class DnsRecord:
    lookup: str  # TODO rename name
    type: DnsRecordType
    data: str
    caa_tag: typing.Optional[str] = None
    caa_flag: typing.Optional[int] = None
    customer_id: typing.Optional[int] = None
    domain_id: typing.Optional[int] = None
    domain_name: typing.Optional[str] = None
    id: typing.Optional[str] = None
    port: typing.Optional[int] = None
    priority: typing.Optional[int] = None
    region_id: typing.Optional[int] = None
    ttl: typing.Optional[int] = None
    weight: typing.Optional[int] = None
    # TODO service_name ??

    @staticmethod
    def from_dict(d: dict) -> "DnsRecord":
        return DnsRecord(
            lookup=d["lookup"],
            type=DnsRecordType(d["type"]),
            data=d["data"],
            caa_tag=d.get("caatag"),
            caa_flag=d.get("caaflag"),
            customer_id=dicthelp.get_first(
                d, ["customerid", "customerId", "customerID"]
            ),
            domain_id=dicthelp.get_first(d, ["domainid", "domainId", "domainID"]),
            domain_name=d.get("name"),
            id=d.get("id"),
            port=d.get("port"),
            priority=d.get("priority"),
            region_id=dicthelp.get_first(d, ["regionid", "regionId", "regionID"]),
            ttl=d.get("ttl"),
            weight=d.get("weight"),
        )

    def to_dict(self) -> dict:
        d = {
            "type": str(self.type),
            "lookup": self.lookup,
            "data": self.data,
        }

        if self.domain_id:
            d["domainid"] = self.domain_id
            d["domainId"] = self.domain_id
            d["domainID"] = self.domain_id
        elif self.domain_name:
            d["name"] = self.domain_name

        opts = {
            "id": self.id,
            "caatag": self.caa_tag,
            "caaflag": self.caa_flag,
            "customerid": self.customer_id,
            "customerId": self.customer_id,
            "customerID": self.customer_id,
            "port": self.port,
            "priority": self.priority,
            "regionid": self.region_id,
            "regionId": self.region_id,
            "regionID": self.region_id,
            "ttl": self.ttl,
            "weight": self.weight,
        }
        for key, value in opts.items():
            if value is not None:
                d[key] = value

        return d


@dataclasses.dataclass
class DnsDomain:
    id: int
    customer_id: int
    serial: str
    stdname: str
    name: str
    type: str
    last_modified: int
    records: list[DnsRecord] = dataclasses.field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "DnsDomain":
        dom = DnsDomain(
            id=d["id"],
            customer_id=dicthelp.get_first(
                d, ["customerid", "customerId", "customerID"]
            ),
            serial=d.get("serial"),
            stdname=d.get("stdname"),
            name=d.get("name"),
            type=d.get("type"),
            last_modified=d.get("lastmodified"),
            records=[],
        )

        for r in d.get("records", []):
            dom.records.append(DnsRecord.from_dict(r))

        return dom


class _dnsOperations:

    def __init__(self, api: api._api):
        self._api = api

    def domain_getall(self) -> list[DnsDomain]:
        """
        Get all domains from the Rackcorp API.

        :return: A list of domains.
        """
        response = self._api.api_get("dns/domain")
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)

        doms = []
        for dom in d.get("data", []):
            doms.append(DnsDomain.from_dict(dom))
        return doms

    def domain_get(self, domain_id: str) -> DnsDomain:
        """
        Get a single domain from the Rackcorp API.

        :return: A domains with a list of records.
        """
        response = self._api.api_get(f"dns/domain/{domain_id}")
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)
        return DnsDomain.from_dict(d["data"])

    def record_get(self, record_id: str) -> DnsRecord:
        """
        Get a single DNS record from the Rackcorp API.

        :return: A record.
        """
        response = self._api.api_get(f"dns/records/{record_id}")
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)
        return DnsRecord.from_dict(d["data"])

    def record_delete(self, record_id: str) -> None:
        """
        Delete a single DNS record from the Rackcorp API.

        :return: None.
        """
        response = self._api.api_legacy_post(
            {
                "cmd": "dns.record.delete",
                # "data": {
                #     record_id: {},
                # },
                "id": record_id,
            }
        )
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)
        return None

    def record_create(self, record: DnsRecord) -> DnsRecord:
        """
        Create a new DNS record in the Rackcorp API.

        :return: The created record.
        """
        d = record.to_dict()

        if "domainid" not in d and "name" not in d:
            raise ValueError("Either domain_id or domain_name must be provided")

        req_body = {"cmd": "dns.record.create", "data": {0: d}}

        response = self._api.api_legacy_post(req_body)
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)
        return DnsRecord.from_dict(d["data"][0])

    def record_update(self, record: DnsRecord) -> DnsRecord:
        """
        Update an existing DNS record in the Rackcorp API.

        :return: The updated record.
        """
        d = record.to_dict()

        req_body = {"cmd": "dns.record.update", "data": {record.id: d}}

        response = self._api.api_legacy_post(req_body)
        if response.status_code != 200:
            self._api.raise_request_exception(response)

        d = response.json()
        self._api.raise_if_json_code_not_ok(d)
        return DnsRecord.from_dict(d["data"][0])
