"""
Contains all needed checks for the required installed apps
"""
from django.apps import apps
from django.core.checks import Error


class Tags:     # pylint: disable=R0903
    """
    Class for tags of registered check functions
    """
    required_installed_apps = "required_installed_apps"


def check_for_required_installed_apps(app_configs, **kwargs):
    """
    Check if the required apps are installed.
    :returns: errors list if the required apps are not installed.
    """
    errors = []

    if not apps.is_installed("sorl.thumbnail"):
        errors.append(
            Error("needs sorl.thumbnail in INSTALLED_APPS", id="wiki_videos.E001")
        )
    return errors
