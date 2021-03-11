# Generated by Django 3.1 on 2021-02-19 04:41

import time
import sys

from django.db import migrations


default_id = '00000000-0000-0000-0000-000000000001'


def add_default_org(apps, schema_editor):
    org_cls = apps.get_model('orgs', 'Organization')
    defaults = {'name': 'DEFAULT', 'id': default_id}
    org_cls.objects.get_or_create(defaults=defaults, id=default_id)


def migrate_default_org_id(apps, schema_editor):
    org_app_models = [
        ('applications', ['Application']),
        ('assets', [
            'AdminUser', 'Asset', 'AuthBook', 'CommandFilter',
            'CommandFilterRule', 'Domain', 'Gateway', 'GatheredUser',
            'Label', 'Node', 'SystemUser'
        ]),
        ('audits', ['FTPLog', 'OperateLog']),
        ('ops', ['AdHoc', 'AdHocExecution', 'CommandExecution', 'Task']),
        ('perms', ['ApplicationPermission', 'AssetPermission', 'UserAssetGrantedTreeNodeRelation']),
        ('terminal', ['Session', 'Command']),
        ('tickets', ['Ticket']),
        ('users', ['UserGroup']),
    ]
    print("")
    for app, models_name in org_app_models:
        for model_name in models_name:
            t_start = time.time()
            print("Migrate model org id: {}".format(model_name), end='')
            sys.stdout.flush()

            model_cls = apps.get_model(app, model_name)
            model_cls.objects.filter(org_id='').update(org_id=default_id)
            interval = round((time.time() - t_start) * 1000, 2)
            print(" done, use {} ms".format(interval))


def add_all_user_to_default_org(apps, schema_editor):
    User = apps.get_model('users', 'User')
    Organization = apps.get_model('orgs', 'Organization')

    users_qs = User.objects.all()
    default_org = Organization.objects.get(id=default_id)

    t_start = time.time()
    count = users_qs.count()
    print(f'Will add users to default org: {count}')

    batch_size = 1000
    for i in range(0, count, batch_size):
        users = list(users_qs[i:i + batch_size])
        default_org.members.add(*users)
        print(f'Add users to default org: {i+1}-{i+len(users)}')
    interval = round((time.time() - t_start) * 1000, 2)
    print(f'done, use {interval} ms')


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0007_auto_20201224_1821'),
        ('audits', '0011_userloginlog_backend'),
        ('ops', '0019_adhocexecution_celery_task_id'),
        ('perms', '0018_auto_20210208_1515'),
        ('applications', '0008_auto_20210104_0435'),
        ('terminal', '0031_auto_20210113_1356'),
        ('users', '0031_auto_20201118_1801'),
        ('assets', '0066_auto_20210208_1802'),
        ('orgs', '0009_auto_20201023_1628'),
    ]

    operations = [
        migrations.RunPython(add_default_org),
        migrations.RunPython(migrate_default_org_id),
        migrations.RunPython(add_all_user_to_default_org)
    ]
