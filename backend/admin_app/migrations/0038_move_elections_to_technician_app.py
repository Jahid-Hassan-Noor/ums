from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("admin_app", "0037_alter_academicevent_created_by_alter_auditlog_user_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterModelTable(name="election", table="technician_app_election"),
                migrations.AlterModelTable(name="schoolelectionseat", table="technician_app_schoolelectionseat"),
                migrations.AlterModelTable(name="electioncandidate", table="technician_app_electioncandidate"),
                migrations.AlterModelTable(name="vote", table="technician_app_vote"),
                migrations.AlterModelTable(name="electionresultsnapshot", table="technician_app_electionresultsnapshot"),
            ],
            state_operations=[
                migrations.DeleteModel(name="Vote"),
                migrations.DeleteModel(name="ElectionResultSnapshot"),
                migrations.DeleteModel(name="ElectionCandidate"),
                migrations.DeleteModel(name="SchoolElectionSeat"),
                migrations.DeleteModel(name="Election"),
            ],
        ),
    ]
