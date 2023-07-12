"""
Django forms for video wiki-plugin
"""
from django import forms
from django.utils.translation import gettext, gettext_lazy as _
from wiki.core.plugins.base import PluginSidebarFormMixin
from wiki.plugins.videos import models


class SidebarForm(PluginSidebarFormMixin):
    """
    Django form for video wiki-plugin sidebar
    """
    def __init__(self, article, request, *args, **kwargs):
        self.article = article
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields["video"].required = True
        self.fields["video"].widget = forms.FileInput(attrs={'accept': 'video/*'})

    def get_usermessage(self):
        return (
                gettext(
                    "New video %s was successfully uploaded. You can use it by selecting it "
                    "from the list of available videos."
                )
                % self.instance.get_filename()
        )

    def save(self, commit=True):
        if not self.instance.id:
            video = models.Video()
            video.article = self.article
            revision = super().save(commit=False)
            revision.set_from_request(self.request)
            video.add_revision(self.instance, save=True)
            return revision
        return super().save(commit=False)

    class Meta:     # pylint: disable=R0903
        """ Metaclass to define corresponding model and chosen fields """
        model = models.VideoRevision
        fields = ("video",)


class RevisionForm(forms.ModelForm):
    """
    Django form for video wiki-plugin revision
    """
    def __init__(self, *args, **kwargs):
        self.video = kwargs.pop("video")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        self.fields["video"].required = True
        self.fields["video"].widget = forms.FileInput(attrs={'accept': 'video/*'})

    def save(self, commit=True):
        if not self.instance.id:
            revision = super().save(commit=False)
            revision.inherit_predecessor(self.video, skip_video_file=True)
            revision.deleted = False  # Restore automatically if deleted
            revision.set_from_request(self.request)
            self.video.add_revision(self.instance, save=True)
            return revision
        return super().save(commit=False)

    class Meta:     # pylint: disable=R0903
        """ Metaclass to define corresponding model and chosen fields """
        model = models.VideoRevision
        fields = ("video",)


class PurgeForm(forms.Form):
    """
    Django form for video wiki-plugin completely remove/purge
    """
    confirm = forms.BooleanField(label=_("Are you sure?"), required=False)

    def clean_confirm(self):
        """ Check if user confirmed purge process """
        confirm = self.cleaned_data["confirm"]
        if not confirm:
            raise forms.ValidationError(gettext("You are not sure enough!"))
        return confirm
