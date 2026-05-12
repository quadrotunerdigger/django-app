from django.contrib.auth.models import Group
from rest_framework.decorators import api_view
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, extend_schema_view

from .serializers import GroupsListSerializer


@extend_schema(
    summary='Hello World',
    description='Возвращает приветственное сообщение.',
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
)
@api_view()
def hello_world_view(request: Request) -> Response:
    return Response({'message': 'Hello World!'})

@extend_schema_view(
    get=extend_schema(
        summary='Список групп',
        description='Возвращает список всех групп пользователей.',
    ),
    post=extend_schema(
        summary='Создать группу',
        description='Создаёт новую группу пользователей.',
    ),
)
class GroupsListView(ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupsListSerializer
