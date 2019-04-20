# Generated by Django 2.1.7 on 2019-04-20 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0007_domain_url_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='DomainTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='domain',
            name='domain_tags',
            field=models.ManyToManyField(related_name='domains', to='articles.DomainTag'),
        ),
    ]