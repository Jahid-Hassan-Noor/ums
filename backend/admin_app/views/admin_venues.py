from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_app import models
from auth_app.permissions import IsAdminRole
from admin_app.serializers import BuildingSerializer, VenueSerializer
from core.common.errors import first_error as _first_error


class AdminVenues(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        buildings = models.Building.objects.all().order_by("name")
        venues = models.Venue.objects.all().order_by("name")
        
        return Response(
            {
                "title": "Venues & Infrastructure",
                "section": "admin",
                "buildings": BuildingSerializer(buildings, many=True).data,
                "venues": VenueSerializer(venues, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AdminBuildingsView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = BuildingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        building = serializer.save()
        return Response(
            {
                "message": "Building created successfully.",
                "building": BuildingSerializer(building).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminBuildingDetailView(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            building = models.Building.objects.get(pk=pk)
        except models.Building.DoesNotExist:
            return Response(
                {"detail": "Building not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        serializer = BuildingSerializer(building, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        building = serializer.save()
        return Response(
            {
                "message": "Building updated successfully.",
                "building": BuildingSerializer(building).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            building = models.Building.objects.get(pk=pk)
        except models.Building.DoesNotExist:
            return Response(
                {"detail": "Building not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        building.delete()
        return Response(
            {"message": "Building deleted successfully."},
            status=status.HTTP_200_OK,
        )


class AdminVenuesCRUDView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = VenueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        venue = serializer.save()
        return Response(
            {
                "message": "Venue created successfully.",
                "venue": VenueSerializer(venue).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminVenueDetailView(APIView):
    permission_classes = [IsAdminRole]

    def put(self, request, pk):
        try:
            venue = models.Venue.objects.get(pk=pk)
        except models.Venue.DoesNotExist:
            return Response(
                {"detail": "Venue not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        serializer = VenueSerializer(venue, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": _first_error(serializer.errors), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        venue = serializer.save()
        return Response(
            {
                "message": "Venue updated successfully.",
                "venue": VenueSerializer(venue).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        try:
            venue = models.Venue.objects.get(pk=pk)
        except models.Venue.DoesNotExist:
            return Response(
                {"detail": "Venue not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
            
        venue.delete()
        return Response(
            {"message": "Venue deleted successfully."},
            status=status.HTTP_200_OK,
        )
