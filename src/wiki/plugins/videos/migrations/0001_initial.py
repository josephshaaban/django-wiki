# Generated by Django 2.2.4 on 2021-03-22 15:14

from django.db import migrations, models
import django.db.models.deletion
import wiki.plugins.videos.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wiki', '0003_mptt_upgrade'),
    ]

    operations = [
        migrations.CreateModel(
            name='Video',
            fields=[
                ('revisionplugin_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wiki.RevisionPlugin')),
            ],
            options={
                'verbose_name': 'video',
                'verbose_name_plural': 'videos',
                'db_table': 'wiki_videos_video',
            },
            bases=('wiki.revisionplugin',),
        ),
        migrations.CreateModel(
            name='VideoRevision',
            fields=[
                ('revisionpluginrevision_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wiki.RevisionPluginRevision')),
                ('video', models.FileField(blank=True, max_length=2000, null=True, upload_to=wiki.plugins.videos.models.upload_path)),
                ('width', models.PositiveIntegerField(blank=True, null=True)),
                ('height', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'video revision',
                'verbose_name_plural': 'video revisions',
                'db_table': 'wiki_videos_videorevision',
                'ordering': ('-created',),
            },
            bases=('wiki.revisionpluginrevision',),
        ),
    ]
