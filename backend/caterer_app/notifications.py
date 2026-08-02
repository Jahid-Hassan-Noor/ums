from admin_app.models import Profile
from caterer_app.service import active_students
from notifications_package.service import notify_profile, notify_profiles, notify_roles


def notify_balance_adjusted(student, adjustment, account, actor):
    notify_profile(
        student,
        actor=actor,
        event_type="canteen.balance_adjusted",
        verb=f"RM {str(adjustment.amount)} was added to your canteen balance.",
        data={
            "adjustment_id": adjustment.id,
            "amount": str(adjustment.amount),
            "reason": adjustment.reason,
            "balance": str(account.balance),
        },
        url="/student/dashboard",
    )


def notify_allowance_policy_updated(*, actor, changes, data):
    verb = f"Canteen {' and '.join(changes)} updated."
    notify_roles(
        [Profile.ROLE_CATERER],
        actor=actor,
        event_type="canteen.policy_updated",
        verb=verb,
        data=data,
        url="/caterer/dashboard",
    )
    notify_profiles(
        active_students(),
        actor=actor,
        event_type="canteen.allowance_updated",
        verb=verb,
        data=data,
        url="/student/dashboard",
    )
