"""
All required django models for videos wiki-plugin
"""
import os.path
import uuid

from django.conf import settings as django_settings
from django.db import models
from django.db.models import signals
from django.utils.translation import gettext, gettext_lazy as _
from wiki.models import RevisionPlugin, RevisionPluginRevision

from . import settings


def upload_path(instance, filename):
    """ Generate/Compose upload path """
    # Has to match original extension filename
    upload_path_ = settings.VIDEO_PATH
    upload_path_ = upload_path_.replace("%aid", str(instance.plugin.video.article.id))
    if settings.VIDEO_PATH_OBSCURIFY:
        upload_path_ = os.path.join(upload_path_, uuid.uuid4().hex)
    return os.path.join(upload_path_, filename)


class Video(RevisionPlugin):
    """ Model for Video """
    def can_write(self, user):
        if not settings.ANONYMOUS and (not user or user.is_anonymous):
            return False
        return RevisionPlugin.can_write(self, user)

    def can_delete(self, user):
        return self.can_write(user)

    class Meta:     # pylint: disable=R0903
        """ Metaclass to define custom attributes """
        verbose_name = _("video")
        verbose_name_plural = _("videos")
        db_table = "wiki_videos_video"  # Matches label of upcoming 0.1 release

    def __str__(self):
        if self.current_revision:
            return (
                gettext("Video: %s")
                % self.current_revision.videorevision.get_filename()
            )
        return gettext("Current revision not set!!")


class VideoRevision(RevisionPluginRevision):
    """ Model for Video Revision """
    # TODO: use VideoField from django-video-encoding or implement it
    #       https://github.com/escaped/django-video-encoding
    video = models.FileField(
        upload_to=upload_path,
        max_length=2000,
        blank=True,
        null=True,
        storage=settings.STORAGE_BACKEND,
    )

    # TODO:
    #  - if we want to generate and save a thumbnail for the uploaded video,
    #       we should to add thumbnail field as ImageField
    #       (this need a service to do this in background)
    #  - add duration field
    #  - update and save width/height manually when saving or doing revision
    width = models.PositiveIntegerField(blank=True, null=True)
    height = models.PositiveIntegerField(blank=True, null=True)

    def get_filename(self):
        """ Used to retrieve the file name and not cause exceptions. """
        if self.video:
            try:
                return self.video.name.split("/")[-1]
            except OSError:
                pass
        return None

    def get_size(self):
        """ Used to retrieve the file size and not cause exceptions. """
        try:
            return self.video.size
        except (ValueError, OSError):
            return None

    def inherit_predecessor(self, video, skip_video_file=False):    # pylint: disable=W0221
        """
        Inherit certain properties from predecessor because it's very
        convenient. Remember to always call this method before
        setting properties :)
        A revision may not have a predecessor if the property is unset, it may
        be unset if it's the initial history entry.
        """
        predecessor = video.current_revision.videorevision
        super().inherit_predecessor(video)
        self.plugin = predecessor.plugin
        self.deleted = predecessor.deleted
        self.locked = predecessor.locked
        if not skip_video_file:
            try:
                self.video = predecessor.video
                self.width = predecessor.width
                self.height = predecessor.height
            except IOError:
                self.video = None

    # TODO: Override this setting with app_label = '' in your extended model
    class Meta:     # pylint: disable=R0903
        """ Metaclass to define custom attributes """
        verbose_name = _("video revision")
        verbose_name_plural = _("video revisions")
        # Matches label of upcoming 0.1 release
        db_table = "wiki_videos_videorevision"
        ordering = ("-created",)

    def __str__(self):
        if self.revision_number:
            return gettext("Vsideo Revision: %d") % self.revision_number
        return gettext("Current revision not set!!")


def on_video_revision_delete(instance, *args, **kwargs):
    """ Delete video file from storage before database deletion """
    if not instance.video:
        return

    path = None
    try:
        path = os.path.dirname(instance.video.path)
    except NotImplementedError:
        # This backend storage doesn't implement 'path' so there is no path to delete
        pass
    except ValueError:
        # in case of Value error
        # https://github.com/django-wiki/django-wiki/issues/936
        pass
    finally:
        # Remove video file
        instance.video.delete(save=False)

    if path is None:
        # This backend storage doesn't implement 'path' so there is no path to delete
        # or some other error (ValueError)
        return

    # Clean up empty directories

    # Check for empty folders in the path. Delete the first two.
    if len(path[-1]) == 32:
        # Path was (most likely) obscurified so we should look 2 levels down
        max_depth = 2
    else:
        max_depth = 1
    for depth in range(0, max_depth):
        delete_path = "/".join(path[:-depth] if depth > 0 else path)
        try:
            dir_list = os.listdir(os.path.join(django_settings.MEDIA_ROOT, delete_path))
        except OSError:
            # Path does not exist, so let's not try to remove it...
            dir_list = None
        if not (dir_list is None) and len(dir_list) == 0:
            os.rmdir(delete_path)


signals.pre_delete.connect(on_video_revision_delete, VideoRevision)
