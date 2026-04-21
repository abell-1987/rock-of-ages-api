from django.http import HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from django.contrib.auth.models import User
from rockapi.models import Rock, Type


class RockTypeSerializer(serializers.ModelSerializer):
    """JSON serializer for rock types"""

    class Meta:
        model = Type
        fields = ("label",)


class RockUserSerializer(serializers.ModelSerializer):
    """Serializer for the user who owns the rock"""

    class Meta:
        model = User
        fields = ("first_name", "last_name")


class RockSerializer(serializers.ModelSerializer):
    """JSON serializer"""

    type = RockTypeSerializer(many=False)
    user = RockUserSerializer(many=False)

    class Meta:
        model = Rock
        fields = (
            "id",
            "name",
            "weight",
            "user",
            "type",
        )


class RockView(ViewSet):
    """Rock view set"""

    def create(self, request):
        """Handle POST requests for rocks"""

        chosen_type = Type.objects.get(pk=request.data["typeId"])

        rock = Rock()
        rock.user = request.auth.user
        rock.weight = request.data["weight"]
        rock.name = request.data["name"]
        rock.type = chosen_type
        rock.save()

        serialized = RockSerializer(rock, many=False)
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        """Handle GET requests for all items"""

        owner_only = request.query_params.get("owner", None)

        try:
            rocks = Rock.objects.all()

            if owner_only is not None and owner_only == "current":
                rocks = rocks.filter(user=request.auth.user)

            serializer = RockSerializer(rocks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single rock"""

        try:
            rock = Rock.objects.get(pk=pk)
        except Rock.DoesNotExist:
            return Response(
                {"message": "Rock not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if rock.user.id == request.auth.user.id:
            rock.delete()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"message": "You do not own that rock"},
                status=status.HTTP_403_FORBIDDEN,
            )
