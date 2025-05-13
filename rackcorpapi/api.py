import configparser
import dataclasses
import enum
import logging
import os
import platform
import requests
import requests.auth
import typing

logger = logging.getLogger(__name__)


class DnsRecordStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


class DnsRecordType(enum.StrEnum):
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
    lookup: str
    type: DnsRecordType
    data: str
    domain_id: typing.Optional[int] = None
    domain_name: typing.Optional[str] = None
    status: DnsRecordStatus = DnsRecordStatus.ACTIVE
    ttl: typing.Optional[int] = None
    region_id: typing.Optional[int] = None
    priority: typing.Optional[int] = None
    weight: typing.Optional[int] = None
    port: typing.Optional[int] = None
    caa_tag: typing.Optional[str] = None
    caa_flag: typing.Optional[int] = None
    customer_id: typing.Optional[int] = None
    # TODO serviceName ??


class ApiCredential:
    """
    Rackcorp API credentials class to hold API key and secret.
    """

    def __init__(self, api_uuid: str, api_secret: str):
        """
        Initialize the ApiCredential class with API uuid and secret.

        :param api_uuid: The API key uuid for authentication.
        :param api_secret: The API key secret for authentication.
        """
        self.api_uuid = api_uuid
        self.api_secret = api_secret

    def http_basic_auth(self) -> requests.auth.HTTPBasicAuth:
        """
        Get HTTP Basic Authentication for the API credentials.

        :return: An instance of HTTPBasicAuth with the API credentials.
        """
        return requests.auth.HTTPBasicAuth(self.api_uuid, self.api_secret)


def get_api_credentials() -> ApiCredential:
    """
    Find API credentials in the execution environment.
    :return: An instance of RackcorpApiCredential with loaded credentials or None.
    """
    api_uuid = os.getenv("RACKCORP_API_UUID", "").strip()
    api_secret = os.getenv("RACKCORP_API_SECRET", "").strip()
    if api_uuid and api_secret:
        return ApiCredential(api_uuid, api_secret)

    config_paths = [
        os.path.expanduser("~/.rackcorp"),
        os.path.expanduser("~/.config/rackcorp/config"),
    ]
    for path in config_paths:
        if os.path.exists(path):
            config = configparser.ConfigParser()
            config.read(path)
            if config and "general" in config:
                api_uuid = config["general"].get("apiuuid", "").strip()
                api_secret = config["general"].get("apisecret", "").strip()
                if api_uuid and api_secret:
                    return ApiCredential(api_uuid, api_secret)

    return None


class Client:
    """
    Rackcorp API class to interact with the Rackcorp API.
    """

    def __init__(
        self,
        cred: ApiCredential = None,
        base_url: str = "https://api.rackcorp.net/api/",
        api_version: str = "v2.8",
        user_agent: str = None,
    ):
        """
        Initialize the RackcorpApi class with an API credential

        :param cred: The API credentials
        """
        if cred is None:
            cred = get_api_credentials()
        if cred is None:
            raise ValueError("Rackcorp API credentials are required")

        if not base_url.endswith("/"):
            base_url += "/"

        if user_agent is None:
            user_agent = f"rackcorpapi/0.1 python/{platform.python_version()}"

        self.cred = cred
        self.base_url = base_url
        self.api_version = api_version
        self.user_agent = user_agent
        self.session = requests.Session()

    def _api_request(
        self, method: str, url_suffix: str, req_body=None
    ) -> requests.Response:
        headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        req = requests.Request(
            method,
            self.base_url + url_suffix,
            headers=headers,
            auth=self.cred.http_basic_auth(),
            json=req_body,
        )
        prep = req.prepare()
        logging.debug(f"request: {prep.method} {prep.url}")
        resp = self.session.send(
            prep,
            timeout=30,  # seconds
        )
        logging.debug(f"response: {resp.status_code}")
        return resp

    def _api_get(self, url_suffix: str) -> requests.Response:
        return self._api_request("GET", f"{self.api_version}/{url_suffix}")

    def _api_delete(self, url_suffix: str) -> requests.Response:
        return self._api_request("DELETE", f"{self.api_version}/{url_suffix}")

    def _api_post(self, url_suffix: str, req_body) -> requests.Response:
        return self._api_request("POST", f"{self.api_version}/{url_suffix}", req_body)

    def _api_legacy_post(self, req_body) -> requests.Response:
        return self._api_request("POST", f"rest/{self.api_version}/json.php", req_body)

    def _raise_request_exception(self, response: requests.Response):
        response.raise_for_status()
        raise requests.RequestException(
            f"Error {response.status_code}: {response.text}", response=response
        )

    def dns_domain_getall(self):
        """
        Get all domains from the Rackcorp API.

        :return: A list of domains.
        """
        response = self._api_get("dns/domain")
        if response.status_code != 200:
            self._raise_request_exception(response)

        return response.json()["data"]

    def dns_domain_get(self, domain_id: str):
        """
        Get a single domain from the Rackcorp API.

        :return: A domains with a list of records.
        """
        response = self._api_get(f"dns/domain/{domain_id}")
        if response.status_code != 200:
            self._raise_request_exception(response)

        return response.json()["data"]

    def dns_record_get(self, record_id: str):
        """
        Get a single DNS record from the Rackcorp API.

        :return: A record.
        """
        response = self._api_get(f"dns/records/{record_id}")
        if response.status_code != 200:
            self._raise_request_exception(response)

        return response.json()["data"]

    def dns_record_delete(self, record_id: str):
        """
        Delete a single DNS record from the Rackcorp API.

        :return: A record.
        """
        response = self._api_legacy_post(
            {
                "cmd": "dns.record.delete",
                # "data": {
                #     record_id: {},
                # },
                "id": record_id,
            }
        )
        if response.status_code != 200:
            self._raise_request_exception(response)

        return response.json()["data"]

    def _dns_record_to_dict(self, record: DnsRecord) -> dict:
        d = {
            "type": str(record.type),
            "lookup": record.lookup,
            "data": record.data,
        }

        if record.domain_id:
            d["domainid"] = record.domain_id
            d["domainId"] = record.domain_id
            d["domainID"] = record.domain_id
        elif record.domain_name:
            d["name"] = record.domain_name

        opts = {
            "caatag": record.caa_tag,
            "caaflag": record.caa_flag,
            "customerid": record.customer_id,
            "port": record.port,
            "priority": record.priority,
            "regionid": record.region_id,
            "ttl": record.ttl,
            "weight": record.weight,
        }
        for key, value in opts.items():
            if value is not None:
                d[key] = value

        return d

    def dns_record_create(self, record: DnsRecord):
        """
        Create a new DNS record in the Rackcorp API.

        :return: The created record.
        """
        d = self._dns_record_to_dict(record)

        if "domainid" not in d and "name" not in d:
            raise ValueError("Either domain_id or domain_name must be provided")

        req_body = {"cmd": "dns.record.create", "data": {0: d}}

        response = self._api_legacy_post(req_body)
        if response.status_code != 200:
            self._raise_request_exception(response)

        return response.json()["data"][0]

    def dns_record_update(self, record: DnsRecord):
        """
        Update an existing DNS record in the Rackcorp API.

        :return: The updated record.
        """
        d = self._dns_record_to_dict(record)

        req_body = {"cmd": "dns.record.update", "data": {record.id: d}}

        response = self._api_legacy_post(req_body)
        if response.status_code != 200:
            self._raise_request_exception(response)
        # TODO if response.json()["code"] != "OK", raise exception with ["message"]

        return response.json()["data"][0]


@dataclasses.dataclass
class BaseApiResponse:
    code: str
    message: str


@dataclasses.dataclass
class DnsDomain:
    id: str
    customerid: str
    serial: str
    stdname: str
    name: str
    type: str
    # slaves: list?
    lastmodified: int
    # clusters: list?


@dataclasses.dataclass
class DnsDomainGetallResponse(BaseApiResponse):
    data: list[DnsDomain] = dataclasses.field(default_factory=list)
