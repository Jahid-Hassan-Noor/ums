import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_app", "0017_alter_profile_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="VenueBookingRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("booking_type", models.CharField(choices=[("event", "Event"), ("personal", "Personal use")], max_length=20)),
                ("purpose", models.CharField(max_length=255)),
                ("explanation", models.TextField()),
                ("booking_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("rejection_reason", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("requester", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="venue_booking_requests", to="admin_app.profile")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_venue_booking_requests", to="admin_app.profile")),
                ("venue", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="booking_requests", to="admin_app.venue")),
            ],
            options={
                "ordering": ("-created_at",),
                "indexes": [models.Index(fields=["venue", "booking_date", "status"], name="admin_app_v_venue_i_70b10d_idx")],
            },
        ),
    ]
