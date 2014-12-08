"""
Overview of all settings which can be customized.
"""

from future.builtins import str
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.defaultfilters import slugify  # Django 1.4 location
from django.utils.importlib import import_module
from parler import appsettings as parler_appsettings
from parler.utils import normalize_language_code, is_supported_django_language
import os


# Templates
FLUENT_PAGES_BASE_TEMPLATE = getattr(settings, "FLUENT_PAGES_BASE_TEMPLATE", 'fluent_pages/base.html')
FLUENT_PAGES_TEMPLATE_DIR = getattr(settings, 'FLUENT_PAGES_TEMPLATE_DIR', settings.TEMPLATE_DIRS[0] if settings.TEMPLATE_DIRS else None)
FLUENT_PAGES_RELATIVE_TEMPLATE_DIR = getattr(settings, 'FLUENT_PAGES_RELATIVE_TEMPLATE_DIR', True)
AUTHZ_BACKEND_NAME = getattr(settings, 'FLUENT_PAGE_AUTHZ_BACKEND', 'fluent_pages.authz_backend.SimpleBackend')

# User-visible settings
FLUENT_PAGES_DEFAULT_IN_NAVIGATION = getattr(settings, 'FLUENT_PAGES_DEFAULT_IN_NAVIGATION', True)
FLUENT_PAGES_KEY_CHOICES = getattr(settings, 'FLUENT_PAGES_KEY_CHOICES', ())

# Note: the default language setting is used during the migrations
# Allow this module to have other settings, but default to the shared settings
FLUENT_DEFAULT_LANGUAGE_CODE = getattr(settings, 'FLUENT_DEFAULT_LANGUAGE_CODE', parler_appsettings.PARLER_DEFAULT_LANGUAGE_CODE)
FLUENT_PAGES_DEFAULT_LANGUAGE_CODE = getattr(settings, 'FLUENT_PAGES_DEFAULT_LANGUAGE_CODE', FLUENT_DEFAULT_LANGUAGE_CODE)
FLUENT_PAGES_LANGUAGES = getattr(settings, 'FLUENT_PAGES_LANGUAGES', parler_appsettings.PARLER_LANGUAGES)

# Performance settings
FLUENT_PAGES_PREFETCH_TRANSLATIONS = getattr(settings, 'FLUENT_PAGES_PREFETCH_TRANSLATIONS', False)

# Advanced settings
FLUENT_PAGES_FILTER_SITE_ID = getattr(settings, 'FLUENT_PAGES_FILTER_SITE_ID', True)
FLUENT_PAGES_PARENT_ADMIN_MIXIN = getattr(settings, 'FLUENT_PAGES_PARENT_ADMIN_MIXIN', None)
FLUENT_PAGES_CHILD_ADMIN_MIXIN = getattr(settings, 'FLUENT_PAGES_CHILD_ADMIN_MIXIN', None)


# Checks
if not FLUENT_PAGES_TEMPLATE_DIR:
    raise ImproperlyConfigured("The setting 'FLUENT_PAGES_TEMPLATE_DIR' or 'TEMPLATE_DIRS[0]' need to be defined!")
else:
    # Clean settings
    FLUENT_PAGES_TEMPLATE_DIR = FLUENT_PAGES_TEMPLATE_DIR.rstrip('/') + '/'

    # Test whether the template dir for page templates exists.
    settingName = 'TEMPLATE_DIRS[0]' if not hasattr(settings, 'FLUENT_PAGES_TEMPLATE_DIR') else 'FLUENT_PAGES_TEMPLATE_DIR'
    if not os.path.isabs(FLUENT_PAGES_TEMPLATE_DIR):
        raise ImproperlyConfigured("The setting '{0}' needs to be an absolute path!".format(settingName))
    if not os.path.exists(FLUENT_PAGES_TEMPLATE_DIR):
        raise ImproperlyConfigured("The path '{0}' in the setting '{1}' does not exist!".format(FLUENT_PAGES_TEMPLATE_DIR, settingName))


def get_page_authz_backend():
    backend_name = AUTHZ_BACKEND_NAME
    try:
        mod, attr = backend_name.rsplit('.', 1)
    except ValueError:
        msg = "Unable to import page authz backend '%s'. "
        msg += "Is it a proper dotted name?"
        raise ImproperlyConfigured(msg % backend_name)

    try:
        module = import_module(mod)
    except ImportError, e:
        msg = 'Error importing CMS authz plugin %s: "%s"'
        raise ImproperlyConfigured(msg % (backend_name, e))
    except ValueError, e:
        msg = 'Error importing CMS authz plugin. Is DEFAULT_AUTHZ_BACKEND a '
        msg += 'correct dotted pathname?'
        raise ImproperlyConfigured(msg)

    try:
        cls = getattr(module, attr)
    except AttributeError:
        msg = 'Module "%s" does not define a "%s" CMS authz backend'
        raise ImproperlyConfigured(msg % (mod, attr))

    return cls()


AUTHZ_BACKEND = get_page_authz_backend()

# Clean settings
FLUENT_PAGES_DEFAULT_LANGUAGE_CODE = normalize_language_code(FLUENT_PAGES_DEFAULT_LANGUAGE_CODE)

if not is_supported_django_language(FLUENT_PAGES_DEFAULT_LANGUAGE_CODE):
    raise ImproperlyConfigured("FLUENT_PAGES_DEFAULT_LANGUAGE_CODE '{0}' does not exist in LANGUAGES".format(FLUENT_PAGES_DEFAULT_LANGUAGE_CODE))

FLUENT_PAGES_LANGUAGES = parler_appsettings.add_default_language_settings(
    FLUENT_PAGES_LANGUAGES, 'FLUENT_PAGES_LANGUAGES',
    hide_untranslated=False,
    hide_untranslated_menu_items=False,
    code=FLUENT_PAGES_DEFAULT_LANGUAGE_CODE,
    fallback=FLUENT_PAGES_DEFAULT_LANGUAGE_CODE
)

# Using a slug field, enforce keys as slugs too.
FLUENT_PAGES_KEY_CHOICES = [(slugify(str(key)), title) for key, title in FLUENT_PAGES_KEY_CHOICES]


def get_language_settings(language_code, site_id=None):
    """
    Return the language settings for the current site
    """
    if site_id is None:
        site_id = settings.SITE_ID

    for lang_dict in FLUENT_PAGES_LANGUAGES.get(site_id, ()):
        if lang_dict['code'] == language_code:
            return lang_dict

    return FLUENT_PAGES_LANGUAGES['default']
