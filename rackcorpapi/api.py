from . import cred
import logging
import requests

logger = logging.getLogger(__name__)


class _api:
    """
    Internal class to interact with the Rackcorp API.
    """

    def __init__(
        self,
        cred: cred.ApiCredential,
        base_url: str,
        api_version: str,
        user_agent: str,
    ):
        if not base_url.endswith("/"):
            base_url += "/"

        self.cred = cred
        self.base_url = base_url
        self.api_version = api_version
        self.user_agent = user_agent
        self.session = requests.Session()

    def api_request(
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

    def api_get(self, url_suffix: str) -> requests.Response:
        return self.api_request("GET", f"{self.api_version}/{url_suffix}")

    def api_delete(self, url_suffix: str) -> requests.Response:
        return self.api_request("DELETE", f"{self.api_version}/{url_suffix}")

    def api_post(self, url_suffix: str, req_body) -> requests.Response:
        return self.api_request("POST", f"{self.api_version}/{url_suffix}", req_body)

    def api_legacy_post(self, req_body) -> requests.Response:
        return self.api_request("POST", f"rest/{self.api_version}/json.php", req_body)

    def raise_request_exception(self, response: requests.Response):
        response.raise_for_status()
        raise requests.RequestException(
            f"Error {response.status_code}: {response.text}", response=response
        )

    def raise_if_json_code_not_ok(self, json_body: dict) -> None:
        code = json_body.get("code")
        msg = json_body.get("message")
        debug = json_body.get("debug")
        if code != "OK":
            if debug:
                logger.debug(f"API error debug info: {debug}")
            raise requests.RequestException(f"Error code '{code}': {msg}")
