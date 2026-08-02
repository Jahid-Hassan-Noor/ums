import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teacher_app", "0010_course_announcement_slots"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="collaboration_mode",
            field=models.CharField(
                choices=[("individual", "Individual"), ("group", "Group")],
                default="individual",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="assignment",
            name="group_rules",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="assignment",
            name="max_group_members",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="assignment",
            name="min_distinct_countries",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="assignment",
            name="require_same_lab_group",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="assignment",
            name="require_same_tutorial_group",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="AssignmentGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="groups",
                        to="teacher_app.assignment",
                    ),
                ),
                (
                    "leader",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="led_assignment_groups",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "ordering": ("name", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("assignment", "name"),
                        name="unique_group_name_per_assignment",
                    ),
                    models.UniqueConstraint(
                        fields=("assignment", "leader"),
                        name="one_led_group_per_student_assignment",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AssignmentGroupMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_memberships",
                        to="teacher_app.assignment",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="teacher_app.assignmentgroup",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_group_memberships",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "ordering": ("joined_at", "id"),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("assignment", "student"),
                        name="one_group_per_student_assignment",
                    ),
                    models.UniqueConstraint(
                        fields=("group", "student"),
                        name="unique_student_in_assignment_group",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AssignmentGroupInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("declined", "Declined"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_invitations",
                        to="teacher_app.assignment",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="teacher_app.assignmentgroup",
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_assignment_group_invitations",
                        to="admin_app.profile",
                    ),
                ),
                (
                    "invitee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignment_group_invitations",
                        to="admin_app.profile",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("group", "invitee"),
                        name="unique_group_invitation_per_student",
                    ),
                ],
            },
        ),
        migrations.AddField(
            model_name="assignmentsubmission",
            name="assignment_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submissions",
                to="teacher_app.assignmentgroup",
            ),
        ),
        migrations.AddField(
            model_name="courseannouncement",
            name="assignment",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="presentation_announcements",
                to="teacher_app.assignment",
            ),
        ),
        migrations.AddField(
            model_name="courseannouncementslotselection",
            name="assignment_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="presentation_slot_selections",
                to="teacher_app.assignmentgroup",
            ),
        ),
        migrations.AddConstraint(
            model_name="courseannouncementslotselection",
            constraint=models.UniqueConstraint(
                condition=models.Q(("assignment_group__isnull", False)),
                fields=("announcement", "assignment_group"),
                name="one_slot_per_group_per_announcement",
            ),
        ),
    ]
