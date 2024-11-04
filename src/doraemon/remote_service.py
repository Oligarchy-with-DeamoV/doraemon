from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Literal
import requests

from dacite import from_dict
from doraemon.logger.slogger import create_logger

logger = create_logger(__name__)


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
        trace_id: str,
        inputs: Dict[str, Any],
        timeout: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict]:

        # get verify settings
        if metadata and metadata.get("verify"):
            verify = metadata["verify"]
        else:
            verify = False

        if not self.check_proto(data=inputs, proto=self.input_proto):
            logger.error(
                "Transform input data to proto failed.",
                proto=self.input_proto,
                data=inputs,
                trace_id=trace_id,
                name=self.name,
            )
            return None

        logger.info(
            "Request remote service.",
            trace_id=trace_id,
            service_url=self.service_url,
            service_method=self.service_method,
            name=self.name,
        )

        request_result = getattr(requests, self.service_method)(
            url=self.service_url,
            params=inputs,
            verify=verify,
            timeout=timeout,
        )

        if not request_result.status_code == 200:
            logger.error(
                "Request remote service failed.",
                status_code=request_result.status_code,
                trace_id=trace_id,
                service_url=self.service_url,
                service_method=self.service_method,
                inputs=inputs,
                name=self.name,
            )
            return None

        request_result = request_result.json()

        if not self.check_proto(request_result, self.output_proto):
            logger.error(
                "Transform output data to proto failed.",
                proto=self.output_proto,
                data=request_result,
                trace_id=trace_id,
                name=self.name,
            )
            return None
        logger.info(
            "Service requests success.",
            trace_id=trace_id,
            service_url=self.service_url,
            service_method=self.service_method,
            inputs=inputs,
            name=self.name,
            outputs=request_result,
        )

        return from_dict(self.output_proto, request_result)
