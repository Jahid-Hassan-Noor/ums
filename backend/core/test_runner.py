import unittest
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.test.runner import DiscoverRunner


class IsolatedCacheTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        test_run_id = uuid4().hex
        self.cache_override = override_settings(
            CACHES={
                alias: {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    "LOCATION": f"ums-tests-{test_run_id}-{alias}",
                }
                for alias in settings.CACHES
            }
        )
        self.cache_override.enable()
        try:
            super().setup_test_environment(**kwargs)
        except Exception:
            self.cache_override.disable()
            raise

    def teardown_test_environment(self, **kwargs):
        try:
            super().teardown_test_environment(**kwargs)
        finally:
            self.cache_override.disable()

    def get_resultclass(self):
        base_class = super().get_resultclass() or unittest.TextTestResult

        class IsolatedCacheResult(base_class):
            def startTest(self, test):
                cache.clear()
                super().startTest(test)

        return IsolatedCacheResult
