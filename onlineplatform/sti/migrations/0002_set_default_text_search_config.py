# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-07 07:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sti', '0001_initial'),
    ]

    operations = [
            migrations.RunSQL("alter database sti set default_text_search_config = 'pg_catalog.english';", reverse_sql=migrations.RunSQL.noop)
    ]
