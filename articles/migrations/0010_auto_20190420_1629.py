# Generated by Django 2.1.7 on 2019-04-20 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0009_domaintag_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domain',
            name='domain_tags',
            field=models.ManyToManyField(blank=True, related_name='domains', to='articles.DomainTag'),
        ),
    ]
