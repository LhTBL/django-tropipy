================
django-tropipy
================

django-tropipy is a Django app to bridge with the www.tropipay.com API and make payments
 in an easy way. Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "tropipy" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "django_tropipy",
    ]

2. Include the tropipy URLconf in your project urls.py like this::

    path("tropipay/", include("django_tropipy.urls")),
