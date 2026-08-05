from admin_app.models import Profile
from admin_app.settings_registry import format_currency_amount
from caterer_app.service import active_students, dining_label
from notifications_package.service import notify_profile, notify_profiles, notify_roles


def notify_balance_adjusted(student, adjustment, account, actor):
    label = dining_label()
    notify_profile(
        student,
        actor=actor,
        event_type="canteen.balance_adjusted",
        verb=f"{format_currency_amount(adjustment.amount)} was added to your {label.lower()} balance.",
        data={
            "adjustment_id": adjustment.id,
            "amount": str(adjustment.amount),
            "reason": adjustment.reason,
            "balance": str(account.balance),
        },
        url="/student/dashboard",
    )


def notify_allowance_policy_updated(*, actor, changes, data):
    verb = f"{dining_label()} {' and '.join(changes)} updated."
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
