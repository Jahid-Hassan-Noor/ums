from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import IsHrRole
from core.common.errors import validation_error_response
from hr_app.onboarding_service import (
    OnboardingLinkConflict,
    OnboardingNotFound,
    StaleOnboardingMove,
    board_payload,
    card_history,
    card_payload,
    column_payload,
    create_card,
    create_column,
    link_employee,
    move_card,
    update_column,
)


def _error_response(error):
    if hasattr(error, "message_dict"):
        return validation_error_response(error.message_dict)
    return validation_error_response({"detail": "; ".join(error.messages)})


class HrOnboardingBoard(APIView):
    permission_classes = [IsHrRole]

    def get(self, request):
        return Response(board_payload())


class HrOnboardingCards(APIView):
    permission_classes = [IsHrRole]

    def post(self, request):
        if not isinstance(request.data, dict):
            return validation_error_response({"detail": "Card data must be an object."})
        try:
            card = create_card(actor=request.user.profile, data=request.data)
        except ValidationError as error:
            return _error_response(error)
        return Response({"card": card_payload(card)}, status=status.HTTP_201_CREATED)


class HrOnboardingCardMove(APIView):
    permission_classes = [IsHrRole]

    def post(self, request, card_id):
        if not isinstance(request.data, dict):
            return validation_error_response({"detail": "Move data must be an object."})
        try:
            card = move_card(actor=request.user.profile, card_id=card_id, data=request.data)
        except OnboardingNotFound:
            return Response({"detail": "Staff card was not found."}, status=status.HTTP_404_NOT_FOUND)
        except StaleOnboardingMove:
            return Response(
                {"detail": "This card has moved since it was loaded. Refresh the board and try again."},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as error:
            return _error_response(error)
        return Response({"card": card_payload(card)})


class HrOnboardingCardHistory(APIView):
    permission_classes = [IsHrRole]

    def get(self, request, card_id):
        try:
            history = card_history(card_id)
        except OnboardingNotFound:
            return Response({"detail": "Staff card was not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(history)


class HrOnboardingCardEmployeeLink(APIView):
    permission_classes = [IsHrRole]

    def post(self, request, card_id):
        if not isinstance(request.data, dict):
            return validation_error_response({"detail": "Employee link data must be an object."})
        try:
            card = link_employee(actor=request.user.profile, card_id=card_id, data=request.data)
        except OnboardingNotFound:
            return Response({"detail": "Staff card was not found."}, status=status.HTTP_404_NOT_FOUND)
        except StaleOnboardingMove:
            return Response(
                {"detail": "This card moved since it was loaded. Refresh the board and try again."},
                status=status.HTTP_409_CONFLICT,
            )
        except OnboardingLinkConflict:
            return Response(
                {"detail": "This card or employee is already linked. Refresh the board and try again."},
                status=status.HTTP_409_CONFLICT,
            )
        except ValidationError as error:
            return _error_response(error)
        return Response({"card": card_payload(card)})


class HrOnboardingColumns(APIView):
    permission_classes = [IsHrRole]

    def post(self, request):
        if not isinstance(request.data, dict):
            return validation_error_response({"detail": "Column data must be an object."})
        try:
            column = create_column(request.data)
        except ValidationError as error:
            return _error_response(error)
        return Response({"column": column_payload(column)}, status=status.HTTP_201_CREATED)


class HrOnboardingColumnDetail(APIView):
    permission_classes = [IsHrRole]

    def patch(self, request, column_id):
        if not isinstance(request.data, dict):
            return validation_error_response({"detail": "Column data must be an object."})
        try:
            column = update_column(column_id, request.data)
        except OnboardingNotFound:
            return Response({"detail": "Board column was not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as error:
            return _error_response(error)
        return Response({"column": column_payload(column)})
