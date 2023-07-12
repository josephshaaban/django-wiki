"""
Template tags for videos plugin
"""
from django import template
from wiki.plugins.videos import models, settings

register = template.Library()


@register.filter
def videos_for_article(article):
    """ List all videos which is related to this wiki page """
    return models.Video.objects.filter(     # pylint: disable=E1101
        article=article, current_revision__deleted=False
    ).order_by("-current_revision__created")


@register.filter
def videos_can_add(article, user):
    """ Check if the current user can add videos to this wiki page """
    if not settings.ANONYMOUS and (not user or user.is_anonymous):
        return False
    return article.can_write(user)
