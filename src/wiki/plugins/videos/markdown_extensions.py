"""
Videos plugin markdown extension with its patterns and processors for Django-wiki.
"""
import re
import markdown
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from wiki.core.markdown import add_to_registry

from wiki.plugins.videos import models, settings


VIDEO_RE = (
    r"(?:"
    +
    # Match '[video:N'
    r"\[video\:(?P<id>[0-9]+)"
    +
    # Match optional 'align'
    r"(?:\s+align\:(?P<align>right|left))?"
    +
    # Match optional 'size'
    r"(?:\s+size\:(?P<size>default|small|medium|large|orig))?"
    +
    # Match ']' and rest of line.
    # Normally [^\n] could be replaced with a dot '.', since '.'
    # does not match newlines, but inline processors run with re.DOTALL.
    r"\s*\](?P<trailer>[^\n]*)$"
    +
    # Match zero or more caption lines, each indented by four spaces.
    r"(?P<caption>(?:\n    [^\n]*)*))"
)


class VideoExtension(markdown.Extension):
    """
    Videos plugin markdown extension for django-wiki.
    """
    def extendMarkdown(self, md):
        """
        Add the various processors and patterns to the Markdown Instance.
        :param md: The Markdown instance.
        """
        add_to_registry(
            md.inlinePatterns, "dw-videos", VideoPattern(VIDEO_RE, md), ">link"
        )
        add_to_registry(
            md.postprocessors, "dw-videos-cleanup", VideoPostprocessor(md), ">raw_html"
        )


class VideoPattern(markdown.inlinepatterns.Pattern):
    """
    django-wiki video preprocessor
    Parse text for [video:N align:ALIGN size:SIZE] references.
    This returns how references should be, initially, rendered in markdown.
    For instance:
    [video:id align:left|right]
        This is the caption text maybe with [a link](...)
    So: Remember that the caption text is fully valid markdown!
    """
    def __init__(self, pattern, md=None):
        """Override init in order to add IGNORECASE and MULTILINE flags"""
        super().__init__(pattern, md=md)
        self.compiled_re = re.compile(
            r"^(.*?)%s(.*)$" % pattern,
            flags=re.DOTALL | re.UNICODE | re.IGNORECASE | re.MULTILINE,
        )
    
    def handleMatch(self, m):
        """
        Return an ElementTree element from the given match.
        :param m: A re match object containing a match of the pattern.
        """
        video = None
        size = settings.VIDEO_RESOLUTIONS['default']

        video_id = m.group("id").strip() if m.group("id") else None
        alignment = m.group("align") if m.group("align") else None
        if m.group("size"):
            size = settings.VIDEO_RESOLUTIONS[m.group("size")]
        try:
            video = models.Video.objects.get(   # pylint: disable=E1101
                article=self.markdown.article,
                id=video_id,
                current_revision__deleted=False,
            )
        except ObjectDoesNotExist:
            pass

        caption = m.group("caption")
        trailer = m.group("trailer")

        caption_placeholder = "{{{VIDEOCAPTION}}}"
        width = size.split("x")[0] if size else "100%"
        html = render_to_string(
            "wiki/plugins/videos/render.html",
            context={
                "video": video,
                "caption": caption_placeholder,
                "align": alignment,
                "width": width,
            }
        )
        html_before, html_after = html.split(caption_placeholder)
        placeholder_before = self.markdown.htmlStash.store(html_before)
        placeholder_after = self.markdown.htmlStash.store(html_after)
        return placeholder_before + caption + placeholder_after + trailer


class VideoPostprocessor(markdown.postprocessors.Postprocessor):
    """
    Postprocessors are run after the ElementTree it converted back into text.

    Each Postprocessor implements a "run" method that takes a pointer to a
    text string, modifies it as necessary and returns a text string.

    Postprocessors must extend markdown.Postprocessor.
    """
    def run(self, text):
        """
        Takes the html document as a single text string and returns a
        modified string for that html document.

        This cleans up after Markdown's well-intended placing of div tags
        inside <p> elements. The problem is that Markdown should put
        <p> tags around div as they are inline elements. However, because
        we wrap them in <div>, we don't actually want it and have to
        remove it again after.
        :param text: the html document as a single text string
        """
        text = text.replace("<p><div", "<div")
        text = text.replace("</div></p>", "</div>")
        return text
