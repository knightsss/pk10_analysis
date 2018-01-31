# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-31 10:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KillPredict',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kill_predict_date', models.CharField(max_length=100)),
                ('kill_predict_time', models.CharField(max_length=100)),
                ('lottery_id', models.IntegerField()),
                ('kill_predict_number', models.CharField(max_length=200)),
                ('lottery_number', models.CharField(max_length=200)),
                ('predict_total', models.IntegerField()),
                ('target_total', models.IntegerField()),
                ('predict_accuracy', models.FloatField()),
            ],
        ),
    ]
