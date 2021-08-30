# -*- coding: utf-8 -*-
from urllib3.exceptions import MaxRetryError

from kubernetes.client import api_client
from kubernetes.client.api import core_v1_api
from kubernetes import client

from common.utils import get_logger

logger = get_logger(__file__)


class KubernetesUtil:
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def get_api(self):
        configuration = client.Configuration()
        configuration.host = self.url
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": "Bearer " + self.token}
        c = api_client.ApiClient(configuration=configuration)
        api = core_v1_api.CoreV1Api(c)
        return api

    def get_namespace_list(self):
        api = self.get_api()
        namespace_list = []
        for ns in api.list_namespace().items:
            namespace_list.append(ns.metadata.name)
        return namespace_list

    def get_services(self):
        api = self.get_api()
        ret = api.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s \t%s \t%s \t%s \t%s \n" % (
                i.kind, i.metadata.namespace, i.metadata.name, i.spec.cluster_ip, i.spec.ports))

    def get_pod_info(self, namespace, pod):
        api = self.get_api()
        resp = api.read_namespaced_pod(namespace=namespace, name=pod)
        return resp

    def get_pod_logs(self, namespace, pod):
        api = self.get_api()
        log_content = api.read_namespaced_pod_log(pod, namespace, pretty=True, tail_lines=200)
        return log_content

    def get_pods(self):
        api = self.get_api()
        try:
            ret = api.list_pod_for_all_namespaces(watch=False, _request_timeout=(3, 3))
        except MaxRetryError:
            logger.warning('Kubernetes connection timed out')
            return
        data = {}
        for i in ret.items:
            namespace = i.metadata.namespace
            pod_info = {
                'pod_name': i.metadata.name,
                'containers': [j.name for j in i.spec.containers]
            }
            if namespace in data:
                data[namespace].append(pod_info)
            else:
                data[namespace] = [pod_info, ]
        return data
