from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from admin_app.models import HostelRoom, Profile, SystemSetting
from admin_app.settings_registry import invalidate_settings_cache, setting_key


User = get_user_model()


class HostelPolicyTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="hostel_policy_admin",
            password="StrongPass123!",
        )
        self.admin_user.profile.role = Profile.ROLE_ADMIN
        self.admin_user.profile.save(update_fields=["role", "updated_at"])

        self.client = APIClient()
        self.client.force_authenticate(self.admin_user)

    def tearDown(self):
        invalidate_settings_cache()

    def update_policy(self, **values):
        SystemSetting.objects.update_or_create(
            key=setting_key("hostel_policy"),
            defaults={"value": values},
        )
        invalidate_settings_cache()

    def test_custom_residence_type_labels_are_used_by_hostel_api(self):
        self.update_policy(
            residence_type_options="staff|Staff housing\nfamily|Family apartments",
        )

        response = self.client.post(
            "/admin/hostels/hostels",
            {
                "code": "STF",
                "name": "Staff Village",
                "hostel_type": "staff",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["hostel"]["hostel_type"], "staff")
        self.assertEqual(response.data["hostel"]["hostel_type_label"], "Staff housing")

        list_response = self.client.get("/admin/hostels")

        self.assertEqual(list_response.status_code, 200)
        self.assertIn(
            {"value": "family", "label": "Family apartments"},
            list_response.data["policy"]["residence_types"],
        )

    def test_room_defaults_max_capacity_format_and_manual_code_override(self):
        self.update_policy(
            residence_type_options="mixed|Mixed residence",
            default_room_capacity=3,
            max_room_capacity=5,
            room_code_format="{hostel_lower}-{floor_raw}-{room_raw}",
            bed_assignment_rule="room_only",
        )
        hostel = self.client.post(
            "/admin/hostels/hostels",
            {"code": "MX", "name": "Mixed Residence", "hostel_type": "mixed"},
            format="json",
        ).data["hostel"]

        room_response = self.client.post(
            "/admin/hostels/rooms",
            {"hostel": hostel["id"], "floor": 2, "number": "7"},
            format="json",
        )

        self.assertEqual(room_response.status_code, 201)
        self.assertEqual(room_response.data["room"]["capacity"], 3)
        self.assertEqual(room_response.data["room"]["code"], "MX-2-7")
        self.assertEqual(room_response.data["room"]["available_sections"], ["MX-2-7"])

        too_large = self.client.post(
            "/admin/hostels/rooms",
            {"hostel": hostel["id"], "floor": 3, "number": "8", "capacity": 6},
            format="json",
        )

        self.assertEqual(too_large.status_code, 400)
        self.assertIn("capacity", too_large.data["errors"])

        manual = self.client.post(
            "/admin/hostels/rooms",
            {
                "hostel": hostel["id"],
                "floor": 4,
                "number": "10",
                "capacity": 2,
                "code": "annex suite 10",
            },
            format="json",
        ).data["room"]

        self.assertEqual(manual["code"], "ANNEX-SUITE-10")

        updated_manual = self.client.put(
            f"/admin/hostels/rooms/{manual['id']}",
            {"hostel": hostel["id"], "floor": 5, "number": "11", "capacity": 2},
            format="json",
        )

        self.assertEqual(updated_manual.status_code, 200)
        self.assertEqual(updated_manual.data["room"]["code"], "ANNEX-SUITE-10")

    def test_generated_room_codes_follow_hostel_code_but_manual_codes_do_not(self):
        self.update_policy(
            residence_type_options="staff|Staff housing",
            room_code_format="{hostel}-{floor}-{room}",
        )
        hostel = self.client.post(
            "/admin/hostels/hostels",
            {"code": "OLD", "name": "Old Staff Block", "hostel_type": "staff"},
            format="json",
        ).data["hostel"]
        generated = self.client.post(
            "/admin/hostels/rooms",
            {"hostel": hostel["id"], "floor": 1, "number": "1", "capacity": 2},
            format="json",
        ).data["room"]
        manual = self.client.post(
            "/admin/hostels/rooms",
            {
                "hostel": hostel["id"],
                "floor": 1,
                "number": "2",
                "capacity": 2,
                "code": "custom-room-2",
            },
            format="json",
        ).data["room"]

        response = self.client.put(
            f"/admin/hostels/hostels/{hostel['id']}",
            {"code": "NEW", "name": "New Staff Block", "hostel_type": "staff"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HostelRoom.objects.get(pk=generated["id"]).code, "NEW-01-01")
        self.assertEqual(HostelRoom.objects.get(pk=manual["id"]).code, "CUSTOM-ROOM-2")
