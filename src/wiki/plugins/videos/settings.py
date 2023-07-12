"""
settings for videos app, a Django-Wiki plugin
"""
from django.conf import settings as django_settings
from wiki.conf import settings as wiki_settings

SLUG = "videos"

# Deprecated
APP_LABEL = None

#: Location where uploaded videos are stored. ``%aid`` is replaced by the article id.
VIDEO_PATH = getattr(django_settings, "WIKI_VIDEOS_PATH", "wiki/videos/%aid/")

# for videos, if we want to generate thumbnails in backend for each uploaded video to display later.
#: Location where uploaded thumbnail for videos are stored. ``%aid`` is replaced by the article id.
THUMBNAIL_PATH = getattr(django_settings, "WIKI_THUMBNAILS_PATH", "wiki/thumbnail/%aid/")

#: Size for the video thumbnail included in the HTML text. If no specific
#: size is given in the markdown tag the ``default`` size is used. If a
#: specific size is given in the markdown tag that size is used.
VIDEO_RESOLUTIONS = getattr(
    django_settings,
    "WIKI_VIDEO_RESOLUTIONS",
    {
        "default": "360x103",
        "small": "180x102",
        "medium": "504x284",
        "large": "720x405",
        "orig": None,
    },
)

#: Storage backend to use, default is to use the same as the rest of the
#: wiki, which is set in ``WIKI_STORAGE_BACKEND``, but you can override it
#: with ``WIKI_VIDEOS_STORAGE_BACKEND``.
STORAGE_BACKEND = getattr(
    django_settings, "WIKI_VIDEOS_STORAGE_BACKEND", wiki_settings.STORAGE_BACKEND
)

#: Should the upload path be obscurified? If so, a random hash will be added
#: to the path such that someone can not guess the location of files (if you
#: have restricted permissions and the files are still located within the
#: web server's file system).
VIDEO_PATH_OBSCURIFY = getattr(django_settings, "WIKI_VIDEOS_PATH_OBSCURIFY", True)

#: Allow anonymous users upload access (not nice on an open network).
#: ``WIKI_VIDEOS_ANONYMOUS`` can override this, otherwise the default
#: in ``wiki.conf.settings`` is used.
ANONYMOUS = getattr(
    django_settings, "WIKI_VIDEOS_ANONYMOUS", wiki_settings.ANONYMOUS_UPLOAD
)

WIKI_MARKDOWN_HTML_ATTRIBUTES = wiki_settings.MARKDOWN_HTML_ATTRIBUTES
WIKI_MARKDOWN_HTML_ATTRIBUTES.update({
    'video': ['class', 'id', 'width', 'height', 'controls'],
    'source': ['class', 'id', 'type', 'src'],
    'track': ['src', 'kind', 'srclang', 'label'],
})
