"""
Admin forms for videos plugin
"""
from django import forms
from django.contrib import admin

from . import models


class VideoForm(forms.ModelForm):
    """ Video admin form """
    class Meta:     # pylint: disable=R0903
        """ Metaclass defines model for this from """
        model = models.Video
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            revisions = models.VideoRevision.objects.filter(plugin=self.instance)   # pylint: disable=E1101
            self.fields["current_revision"].queryset = revisions
        else:
            self.fields[
                "current_revision"
            ].queryset = models.VideoRevision.objects.none()    # pylint: disable=E1101
            self.fields["current_revision"].widget = forms.HiddenInput()


class VideoRevisionInline(admin.TabularInline):
    """ Inline form for VideoRevision model in video admin form"""

    model = models.VideoRevision
    extra = 1
    fields = ("video", "locked", "deleted")



class VideoAdmin(admin.ModelAdmin):
    """ Video admin model """
    form = VideoForm
    inlines = (VideoRevisionInline,)


admin.site.register(models.Video, VideoAdmin)
