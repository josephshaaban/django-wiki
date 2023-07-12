"""
All required views for videos wiki plugin
"""
import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import ListView, FormView, RedirectView
from wiki.conf import settings as wiki_settings
from wiki.core.paginator import WikiPaginator
from wiki.decorators import get_article
from wiki.models import RevisionPluginRevision
from wiki.views.mixins import ArticleMixin

from . import models, forms

logger = logging.getLogger(__name__)


class VideoView(ArticleMixin, ListView):    # pylint: disable=R0901
    """
    View to manage videos and their history
    """
    template_name = "wiki/plugins/videos/index.html"
    allow_empty = True
    context_object_name = "videos"
    paginator_class = WikiPaginator
    paginate_by = 10

    @method_decorator(get_article(can_read=True, not_locked=True))
    def dispatch(self, request, article, *args, **kwargs):
        return super().dispatch(request, article, *args, **kwargs)

    def get_queryset(self):
        if self.article.can_moderate(self.request.user) or self.article.can_delete(
            self.request.user
        ):
            videos = models.Video.objects.filter(article=self.article)  # pylint: disable=E1101
        else:
            videos = models.Video.objects.filter(   # pylint: disable=E1101
                article=self.article, current_revision__deleted=False
            )
        videos.select_related()
        return videos.order_by("-current_revision__videorevision__created")

    def get_context_data(self, **kwargs):
        kwargs.update(ArticleMixin.get_context_data(self, **kwargs))
        return ListView.get_context_data(self, **kwargs)


class DeleteView(ArticleMixin, RedirectView):
    """ View to delete/restore video (soft-delete) """

    permanent = False

    def __init__(self):
        self.video = None
        self.restore = False
        super().__init__()

    @method_decorator(get_article(can_write=True, can_moderate=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.video = get_object_or_404(
            models.Video, article=article, id=kwargs.get('video_id', None)
        )
        self.restore = kwargs.get('restore', False)
        return ArticleMixin.dispatch(self, request, article, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        if not self.video.current_revision:
            logger.critical(
                "Encountered a video without current revision set, ID: %s",
                self.video.id
            )
            latest_revision = RevisionPluginRevision.objects.filter(    # pylint: disable=E1101
                plugin=self.video,
            ).latest("pk")
            self.video.current_revision = latest_revision

        new_revision = models.VideoRevision()
        new_revision.inherit_predecessor(video=self.video)
        new_revision.set_from_request(self.request)
        new_revision.revision_number = RevisionPluginRevision.objects.filter(   # pylint: disable=E1101
            plugin=self.video
        ).count()
        new_revision.delete = not self.restore
        new_revision.save()
        self.video.current_revision = new_revision
        self.video.save()
        if self.restore:
            messages.info(
                self.request, _("%s has been restored") % new_revision.get_filename()
            )
        else:
            messages.info(
                self.request,
                _("%s has been marked as deleted") % new_revision.get_filename(),
            )
        if self.urlpath:
            return reverse("wiki:videos_index", kwargs={'path': self.urlpath.path})
        return reverse("wiki:videos_index", kwargs={"article_id": self.article.id})


class PurgeView(ArticleMixin, FormView):    # pylint: disable=R0901
    """ View to delete video completely with its history """

    template_name = 'wiki/plugins/videos/purge.html'
    permanent = False
    form_class = forms.PurgeForm

    def __init__(self):
        self.video = None
        super().__init__()

    @method_decorator(get_article(can_write=True, can_moderate=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.video = get_object_or_404(
            models.Video, article=article, id=kwargs.get("video_id", None)
        )
        return super().dispatch(request, article, *args, **kwargs)

    def form_valid(self, form):
        for revision in self.video.revision_set.all().select_related('videorevision'):
            revision.videorevision.video.delete(save=False)
            revision.videorevision.delete()

        if self.urlpath:
            return redirect("wiki:videos_index", path=self.urlpath.path)
        return redirect("wiki:videos_index", article_id=self.article.id)

    def get_context_data(self, **kwargs):
        # Needed since Django 1.9 because get_context_data is no longer called
        # with the form instance
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        kwargs = ArticleMixin.get_context_data(self, **kwargs)
        kwargs.update(FormView.get_context_data(self, **kwargs))
        return kwargs


class RevisionChangeView(ArticleMixin, RedirectView):
    """ View to revert to any version of video from history """

    permanent = False

    def __init__(self):
        self.video = None
        self.revision = None
        super().__init__()

    @method_decorator(get_article(can_write=True, not_locked=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.video = get_object_or_404(
            models.Video, article=article, id=kwargs.get("video_id", None)
        )
        self.revision = get_object_or_404(
            models.VideoRevision, plugin__article=article, id=kwargs.get("rev_id", None)
        )
        return ArticleMixin.dispatch(self, request, article, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        self.video.current_revision = self.revision
        self.video.save()
        messages.info(
            self.request,
            _("%(file)s has been changed to revision #%(revision)d")
            % {
                "file": self.video.current_revision.videorevision.get_filename(),
                "revision": self.revision.revision_number,
            },
        )
        if self.urlpath:
            return reverse("wiki:videos_index", kwargs={"path": self.urlpath.path})
        return reverse("wiki:videos_index", kwargs={"article_id": self.article.id})


class RevisionAddView(ArticleMixin, FormView):  # pylint: disable=R0901
    """ View to add new version of video """

    template_name = "wiki/plugins/videos/revision_add.html"
    form_class = forms.RevisionForm

    def __init__(self):
        self.video = None
        super().__init__()

    @method_decorator(get_article(can_write=True, not_locked=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.video = get_object_or_404(
            models.Video, article=article, id=kwargs.get("video_id", None)
        )
        if not self.video.can_write(request.user):
            return redirect(wiki_settings.LOGIN_URL)
        return ArticleMixin.dispatch(self, request, article, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs = super().get_form_kwargs(**kwargs)
        kwargs["video"] = self.video
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        # Needed since Django 1.9 because get_context_data is no longer called
        # with the form instance
        if "form" not in kwargs:
            kwargs["form"] = self.get_form()
        kwargs = super().get_context_data(**kwargs)
        kwargs["video"] = self.video
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.info(
            self.request,
            _("%(file)s has been saved.")
            % {"file": self.video.current_revision.videorevision.get_filename()},
        )
        if self.urlpath:
            return redirect("wiki:edit", path=self.urlpath.path)
        return redirect("wiki:edit", article_id=self.article.id)
