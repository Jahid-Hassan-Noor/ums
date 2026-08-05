from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from admin_app import models
from admin_app.settings_registry import (
    CACHE_KEY,
    SETTINGS_SECTIONS,
    UI_CUSTOMIZATION_DEFAULTS,
    defaults_for_section,
    setting_key,
)
from auth_app.models import prune_role_details


PUBLIC_SETTING_SECTIONS = {
    "general",
    "university",
    "localization",
    "terminology",
    "dashboard",
    "librarian_library",
    "ui_customization",
}


def username_from_email(email):
    return email.split("@", 1)[0].replace(".", "_").replace("+", "_").lower()


def split_name(full_name):
    parts = str(full_name or "").strip().split()
    if not parts:
        return "Portal", "Admin"
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


class Command(BaseCommand):
    help = (
        "Create generic university portal bootstrap defaults without demo "
        "or institution-specific records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-email",
            default="",
            help=(
                "Optionally create or promote a superuser/admin profile for this "
                "email. No admin account is created unless this is supplied."
            ),
        )
        parser.add_argument(
            "--admin-name",
            default="Portal Admin",
            help="Display name for the optional bootstrap admin account.",
        )
        parser.add_argument(
            "--admin-password",
            default="",
            help=(
                "Password for the optional bootstrap admin account. If omitted, a "
                "new optional admin account receives an unusable password."
            ),
        )
        parser.add_argument(
            "--skip-admin-sync",
            action="store_true",
            help="Do not sync existing superusers into admin role profiles.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_email = str(options.get("admin_email") or "").strip().lower()
        admin_password = options.get("admin_password") or ""
        if admin_password and not admin_email:
            raise CommandError("--admin-password requires --admin-email.")

        created, updated = self.seed_settings()
        admin_count = 0

        if admin_email:
            self.ensure_optional_admin(
                email=admin_email,
                full_name=options.get("admin_name") or "Portal Admin",
                password=admin_password,
            )

        if not options.get("skip_admin_sync"):
            admin_count = self.sync_superuser_admin_profiles()

        cache.delete(CACHE_KEY)

        self.stdout.write(
            self.style.SUCCESS(
                "Bootstrapped generic portal defaults: "
                f"{created} settings created, {updated} settings updated, "
                f"{admin_count} superuser admin profile(s) synchronized."
            )
        )

    def seed_settings(self):
        created = 0
        updated = 0
        sections = {
            section: defaults_for_section(section)
            for section in SETTINGS_SECTIONS
        }
        sections["ui_customization"] = deepcopy(UI_CUSTOMIZATION_DEFAULTS)

        for section, defaults in sections.items():
            definition = SETTINGS_SECTIONS.get(
                section,
                {
                    "title": "Portal UI Customization",
                    "description": "Dashboard and public UI defaults.",
                },
            )
            was_created, was_updated = self.upsert_setting_section(
                section=section,
                defaults=defaults,
                description=definition["description"],
                is_public=section in PUBLIC_SETTING_SECTIONS,
            )
            created += int(was_created)
            updated += int(was_updated)
        return created, updated

    def upsert_setting_section(self, section, defaults, description, is_public):
        key = setting_key(section)
        record, created = models.SystemSetting.objects.get_or_create(
            key=key,
            defaults={
                "value": defaults,
                "description": description,
                "is_public": is_public,
            },
        )
        if created:
            return True, False

        existing = record.value if isinstance(record.value, dict) else {}
        merged = {**defaults, **existing}
        update_fields = []
        if merged != record.value:
            record.value = merged
            update_fields.append("value")
        if record.description != description:
            record.description = description
            update_fields.append("description")
        if record.is_public != is_public:
            record.is_public = is_public
            update_fields.append("is_public")

        if update_fields:
            record.save(update_fields=update_fields + ["updated_at"])
            return False, True
        return False, False

    def ensure_optional_admin(self, email, full_name, password):
        User = get_user_model()
        username = username_from_email(email)
        first_name, last_name = split_name(full_name)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user, _created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

        user.email = email
        user.first_name = user.first_name or first_name
        user.last_name = user.last_name or last_name
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        if password:
            user.set_password(password)
        elif not user.has_usable_password():
            user.set_unusable_password()
        user.save()

    def sync_superuser_admin_profiles(self):
        count = 0
        for user in get_user_model().objects.filter(is_superuser=True, is_active=True):
            profile, _created = models.Profile.objects.update_or_create(
                user=user,
                defaults={
                    "role": models.Profile.ROLE_ADMIN,
                    "designation": "System administrator",
                    "is_active": True,
                },
            )
            prune_role_details(profile)
            models.Admin.objects.update_or_create(
                profile=profile,
                defaults={
                    "admin_id": profile.staff_id or username_from_email(user.email or user.username).upper(),
                    "designation": profile.designation or "System administrator",
                    "is_active": True,
                },
            )
            count += 1
        return count
