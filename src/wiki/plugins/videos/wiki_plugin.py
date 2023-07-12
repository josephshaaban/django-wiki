"""
This file is required to register videos plugin into Django-wiki plugins.
"""
from django.urls import re_path
from django.utils.translation import gettext as _
from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.notifications.settings import ARTICLE_EDIT
from wiki.plugins.notifications.util import truncate_title

from wiki.plugins.videos import settings, forms, models
from wiki.plugins.videos.markdown_extensions import VideoExtension

from . import views


class VideoPlugin(BasePlugin):      # pylint: disable=R0903
    """
    Implements Django-wiki BasePlugin class for VideoPlugin.
    """
    slug = settings.SLUG
    sidebar = {
        "headline": _("Videos"),
        "icon_class": "fa-file-video",
        "template": "wiki/plugins/videos/sidebar.html",
        "form_class": forms.SidebarForm,
        "get_form_kwargs": (lambda a: {"instance": models.Video(article=a)}),
    }

    # List of notifications to construct signal handlers for. This
    # is handled inside the notifications plugin.
    notifications = [
        {
            "model": models.VideoRevision,
            "message": lambda obj: _("A video was added: %s")
                                   % truncate_title(obj.get_filename()),
            "key": ARTICLE_EDIT,
            "created": False,
            # Ignore if there is a previous revision... the video isn't new
            "ignore": lambda revision: bool(revision.previous_revision),
            "get_article": lambda obj: obj.article,
        }
    ]

    urlpatterns = {
        "article": [
            re_path("^$", views.VideoView.as_view(), name="videos_index"),
            re_path(
                "^delete/(?P<video_id>[0-9]+)/$",
                views.DeleteView.as_view(),
                name="videos_delete",
            ),
            re_path(
                "^restore/(?P<video_id>[0-9]+)/$",
                views.DeleteView.as_view(),
                name="videos_restore",
                kwargs={"restore": True},
            ),
            re_path(
                "^purge/(?P<video_id>[0-9]+)/$",
                views.PurgeView.as_view(),
                name="videos_purge",
            ),
            re_path(
                "^(?P<video_id>[0-9]+)/revision/change/(?P<rev_id>[0-9]+)/$",
                views.RevisionChangeView.as_view(),
                name="videos_set_revision",
            ),
            re_path(
                "^(?P<video_id>[0-9]+)/revision/add/$",
                views.RevisionAddView.as_view(),
                name="videos_add_revision",
            ),
        ]
    }

    markdown_extensions = [VideoExtension()]


registry.register(VideoPlugin)
