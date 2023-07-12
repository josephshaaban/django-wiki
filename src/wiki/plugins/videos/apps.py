"""
Custom config for videos Django app
"""
from django.apps import AppConfig
from django.core.checks import register
from django.utils.translation import gettext_lazy as _

from . import checks


class VideosConfig(AppConfig):
    """
    AppConfig instance for videos Django app
    """
    name = 'wiki.plugins.videos'
    verbose_name = _("Wiki videos")
    label = "wiki_videos"

    def ready(self):
        register(
            checks.check_for_required_installed_apps,
            checks.Tags.required_installed_apps,
        )
