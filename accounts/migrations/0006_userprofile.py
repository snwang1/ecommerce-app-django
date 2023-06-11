# Generated by Django 4.2 on 2023-05-28 22:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_account_agent_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_picture', models.ImageField(blank=True, upload_to='userprofile')),
                ('address_line_1', models.CharField(blank=True, max_length=100)),
                ('address_line_2', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(max_length=50)),
                ('state', localflavor.us.models.USStateField(max_length=2)),
                ('zip', localflavor.us.models.USZipCodeField(default='XXXXX', max_length=10)),
                ('country', models.CharField(choices=[('US', 'United States of America')], max_length=2)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]