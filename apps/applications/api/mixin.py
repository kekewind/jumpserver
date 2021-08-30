from urllib.parse import urlencode, parse_qsl

from django.utils.translation import ugettext as _
from rest_framework.generics import get_object_or_404

from common.tree import TreeNode
from orgs.models import Organization
from assets.models import SystemUser
from applications.utils import KubernetesUtil
from perms.utils.application.permission import get_application_system_user_ids

from ..models import Application

__all__ = ['SerializeApplicationToTreeNodeMixin']


class SerializeApplicationToTreeNodeMixin:

    @staticmethod
    def filter_organizations(applications):
        organization_ids = set(applications.values_list('org_id', flat=True))
        organizations = [Organization.get_instance(org_id) for org_id in organization_ids]
        organizations.sort(key=lambda x: x.name)
        return organizations

    @staticmethod
    def create_root_node():
        name = _('My applications')
        node = TreeNode(**{
            'id': 'applications',
            'name': name,
            'title': name,
            'pId': '',
            'open': True,
            'isParent': True,
            'meta': {
                'type': 'root'
            }
        })
        return node

    @staticmethod
    def create_system_user_node(tree_id, app_id, user):
        tree_nodes = []
        app = get_object_or_404(Application, id=app_id)
        system_user_ids = get_application_system_user_ids(user, app)
        system_users = SystemUser.objects.filter(id__in=system_user_ids).order_by('priority')
        for system_user in system_users:
            tree_nodes.append(
                Application.as_k8s_system_tree_node(
                    tree_id, system_user
                )
            )
        return tree_nodes

    @staticmethod
    def get_kubernetes_data(app_id, system_user_id):
        app = get_object_or_404(Application, id=app_id)
        system_user = get_object_or_404(SystemUser, id=system_user_id)
        k8s = KubernetesUtil(app.attrs['cluster'], system_user.token)
        return k8s.get_pods()

    def serialize_applications_with_org(self, applications, tree_id, user):
        if not applications:
            return []
        tree_nodes = []
        organizations = self.filter_organizations(applications)
        if not tree_id:
            root_node = self.create_root_node()
            tree_nodes.append(root_node)
            for i, org in enumerate(organizations):
                tree_id = urlencode({'org_id': str(org.id)})
                # 组织节点
                org_node = org.as_tree_node(oid=tree_id, pid=root_node.id)
                tree_nodes.append(org_node)
                apps = applications.filter(org_id=org.id)
                org_node.name += '({})'.format(apps.count())

                tree_nodes += Application.create_category_type_tree_nodes(
                    apps, tree_id, show_empty=False
                )

                for app in apps:
                    if app.type == 'k8s':
                        tree_nodes.append(app.as_k8s_tree_node(tree_id))
                        i, __ = app.create_app_tree_id_pid(tree_id)
                        tree_nodes += self.create_system_user_node(i, app.id, user)
                    else:
                        tree_nodes.append(app.as_tree_node(tree_id))

        else:
            tree_info = dict(parse_qsl(tree_id))
            app_id = tree_info.get('app_id')
            system_user_id = tree_info.get('system_user_id')
            namespace = tree_info.get('namespace')
            pod_name = tree_info.get('pod_name')
            data = self.get_kubernetes_data(app_id, system_user_id)
            if not data:
                return tree_nodes

            if pod_name:
                for container in next(
                        filter(
                            lambda x: x['pod_name'] == pod_name, data[namespace]
                        )
                )['containers']:
                    tree_nodes.append(
                        Application.as_k8s_namespace_pod_tree_node(
                            tree_id, container, 0, type='container', is_container=True
                        )
                    )
            elif namespace:
                for pod in data[namespace]:
                    counts = len(pod['containers'])
                    tree_nodes.append(
                        Application.as_k8s_namespace_pod_tree_node(
                            tree_id, pod['pod_name'], counts, type='pod_name'
                        )
                    )
            elif system_user_id:
                for namespace, pods in data.items():
                    counts = len(pods)
                    tree_nodes.append(
                        Application.as_k8s_namespace_pod_tree_node(
                            tree_id, namespace, counts, type='namespace'
                        )
                    )
        return tree_nodes
