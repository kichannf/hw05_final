# Generated by Django 2.2.16 on 2022-10-18 16:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20221018_2041'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='user_not_author',
        ),
    ]