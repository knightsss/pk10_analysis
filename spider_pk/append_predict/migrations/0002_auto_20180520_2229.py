# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-05-20 14:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('append_predict', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='killpredicttotal',
            name='gain_all_money',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='killpredicttotal',
            name='xiazhu_all_money',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
