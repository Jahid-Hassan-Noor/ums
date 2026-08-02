import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0038_move_elections_to_technician_app"),
        ("auth_app", "0001_initial"),
        ("technician_app", "0004_alter_helpdeskticket_assigned_to_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Election",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("title", models.CharField(max_length=255)),
                        ("description", models.TextField(blank=True)),
                        (
                            "election_type",
                            models.CharField(
                                choices=[("src", "SRC election"), ("school_committee", "School committee election")],
                                default="src",
                                max_length=30,
                            ),
                        ),
                        ("starts_at", models.DateTimeField(blank=True, null=True)),
                        ("ends_at", models.DateTimeField(blank=True, null=True)),
                        ("general_selection_count", models.PositiveSmallIntegerField(default=0)),
                        ("school_selection_count", models.PositiveSmallIntegerField(default=0)),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("draft", "Draft"),
                                    ("upcoming", "Upcoming"),
                                    ("active", "Active"),
                                    ("closed", "Closed"),
                                    ("published", "Published"),
                                ],
                                default="draft",
                                max_length=20,
                            ),
                        ),
                        ("is_active", models.BooleanField(default=False)),
                        ("results_published_at", models.DateTimeField(blank=True, null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        (
                            "created_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="created_elections",
                                to="auth_app.profile",
                            ),
                        ),
                        (
                            "published_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="published_elections",
                                to="auth_app.profile",
                            ),
                        ),
                        (
                            "school",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="committee_elections",
                                to="admin_app.school",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="SchoolElectionSeat",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("seat_count", models.PositiveSmallIntegerField(default=0)),
                        (
                            "election",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="school_seats",
                                to="technician_app.election",
                            ),
                        ),
                        (
                            "school",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="election_seats",
                                to="admin_app.school",
                            ),
                        ),
                    ],
                    options={
                        "unique_together": {("election", "school")},
                    },
                ),
                migrations.CreateModel(
                    name="ElectionCandidate",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("display_name", models.CharField(blank=True, max_length=255)),
                        ("student_identifier", models.CharField(blank=True, max_length=80)),
                        (
                            "category",
                            models.CharField(
                                choices=[("general", "General category"), ("school", "School category")],
                                default="general",
                                max_length=20,
                            ),
                        ),
                        ("details", models.TextField(blank=True)),
                        ("manifesto", models.TextField(blank=True)),
                        ("photo", models.FileField(blank=True, null=True, upload_to="elections/candidates/")),
                        (
                            "status",
                            models.CharField(
                                choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                                default="approved",
                                max_length=20,
                            ),
                        ),
                        ("sort_order", models.PositiveIntegerField(default=0)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "election",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="candidates",
                                to="technician_app.election",
                            ),
                        ),
                        (
                            "school",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="election_candidates",
                                to="admin_app.school",
                            ),
                        ),
                        (
                            "student",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="election_candidates",
                                to="auth_app.profile",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ("election_id", "category", "school__name", "sort_order", "display_name"),
                        "unique_together": {("election", "student", "category")},
                    },
                ),
                migrations.CreateModel(
                    name="Vote",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        (
                            "category",
                            models.CharField(
                                choices=[("general", "General category"), ("school", "School category")],
                                default="general",
                                max_length=20,
                            ),
                        ),
                        ("cast_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "candidate",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="votes",
                                to="technician_app.electioncandidate",
                            ),
                        ),
                        (
                            "election",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="votes",
                                to="technician_app.election",
                            ),
                        ),
                        (
                            "student",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="election_votes",
                                to="auth_app.profile",
                            ),
                        ),
                    ],
                    options={
                        "unique_together": {("election", "student", "candidate")},
                        "indexes": [
                            models.Index(fields=["election", "student", "category"], name="technician__electio_9ec7b4_idx"),
                            models.Index(fields=["candidate", "category"], name="technician__candida_71719e_idx"),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="ElectionResultSnapshot",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("totals", models.JSONField(blank=True, default=dict)),
                        ("published_at", models.DateTimeField(blank=True, null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        (
                            "election",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="result_snapshots",
                                to="technician_app.election",
                            ),
                        ),
                        (
                            "generated_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="auth_app.profile",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ("-created_at",),
                    },
                ),
            ],
        ),
    ]
