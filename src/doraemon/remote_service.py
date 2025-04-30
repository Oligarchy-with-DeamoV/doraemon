from typing import Any, Dict, Literal, Optional

from dacite import from_dict
import requests

import structlog

logger = structlog.getLogger(__name__)


class BaseService:
    def __init__(
        self,
        name: str,
        service_url: str,
        service_method: Literal["post", "get"],
        input_proto: Any,
        output_proto: Any,
    ):
        self.name = name
        self.service_url = service_url
        self.service_method = service_method
        self.input_proto = input_proto
        self.output_proto = output_proto

    def check_proto(self, data, proto) -> bool:
        try:
            from_dict(proto, data)
            return True
        except Exception as e:
            logger.error("check proto failed.", execption=e)
            return False

    def __call__(
        self,
        timeout: float,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:

        # get verify settings
        if metadata and metadata.get("verify"):
            verify = metadata["verify"]
        else:
            verify = False

        _check_data = [x for x in [data, json, params] if x is not None][0]
        if not self.check_proto(data=_check_data, proto=self.input_proto):
            logger.error(
                "Transform input data to proto failed.",
                proto=self.input_proto,
                params=params,
                json=json,
                headers=headers,
                name=self.name,
            )
            return None

        logger.info(
            "Request remote service.",
            json=json,
            params=params,
            headers=headers,
            service_url=self.service_url,
            service_method=self.service_method,
            name=self.name,
        )

        request_result = getattr(requests, self.service_method)(
            url=self.service_url,
            params=params,
            data=data,
            json=json,
            verify=verify,
            headers=headers,
            timeout=timeout,
        )

        if not request_result.status_code == 200:
            logger.error(
                "Request remote service failed.",
                status_code=request_result.status_code,
                headers=headers,
                service_url=self.service_url,
                service_method=self.service_method,
                params=params,
                json=json,
                name=self.name,
            )
            return None

        request_result = request_result.json()

        if not self.check_proto(request_result, self.output_proto):
            logger.error(
                "Transform output data to proto failed.",
                proto=self.output_proto,
                data=request_result,
                headers=headers,
                name=self.name,
            )
            return None
        logger.info(
            "Service requests success.",
            service_url=self.service_url,
            service_method=self.service_method,
            params=params,
            json=json,
            name=self.name,
            outputs=request_result,
        )

        return from_dict(self.output_proto, request_result)
