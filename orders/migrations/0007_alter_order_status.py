# Generated by Django 4.2 on 2023-05-28 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_remove_orderproduct_variation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('open', 'open'), ('complete', 'complete'), ('expired', 'expired')], default='open', max_length=10),
        ),
    ]
