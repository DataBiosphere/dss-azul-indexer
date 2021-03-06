from functools import lru_cache
import json
import boto3
import botocore.session
from typing import Optional, Tuple


def memoized_property(f):
    return property(lru_cache(maxsize=1)(f))


class AWS:
    @memoized_property
    def profile(self):
        session = botocore.session.Session()
        profile_name = session.get_config_variable('profile')
        return session.full_config['profiles'][profile_name]

    @memoized_property
    def region_name(self):
        return self.sts.meta.region_name

    @memoized_property
    def sts(self):
        return boto3.client('sts')

    @memoized_property
    def lambda_(self):
        return boto3.client('lambda')

    @memoized_property
    def apigateway(self):
        return boto3.client('apigateway')

    @memoized_property
    def account(self):
        return self.sts.get_caller_identity()['Account']

    @memoized_property
    def es(self):
        return boto3.client('es')

    def api_gateway_id(self, function_name: str) -> Optional[str]:
        try:
            response = self.lambda_.get_policy(FunctionName=function_name)
        except self.lambda_.exceptions.ResourceNotFoundException:
            return None
        else:
            policy = json.loads(response['Policy'])
            api_stage_arn = policy['Statement'][0]['Condition']['ArnLike']['AWS:SourceArn']
            return api_stage_arn.split(':')[-1].split('/', 1)[0]

    def api_getway_endpoint(self, function_name: str, api_gateway_stage: str) -> Optional[str]:
        api_gateway_id = self.api_gateway_id(function_name)
        if api_gateway_id is None:
            return None
        else:
            return f"https://{api_gateway_id}.execute-api.{self.region_name}.amazonaws.com/{api_gateway_stage}/"

    def es_endpoint(self, es_domain: str) -> Tuple[str, int]:
        es_domain_status = self.es.describe_elasticsearch_domain(DomainName=es_domain)
        return es_domain_status['DomainStatus']['Endpoint'], 443


del memoized_property

aws = AWS()

del AWS
