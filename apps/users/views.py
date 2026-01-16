import logging

from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.helpers import get_client_ip, get_user_agent
from apps.users.paginations import UserPagination
from apps.users.serializers import OTPRequestSerializer, OTPVerifySerializer
from apps.users.services import OTPService

logger = logging.getLogger(__name__)


class OTPRequestView(APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = OTPRequestSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        success, response_data = OTPService.request_otp(email, ip_address, user_agent)
        status_code = status.HTTP_202_ACCEPTED if success else status.HTTP_429_TOO_MANY_REQUESTS
        
        return Response(response_data, status=status_code)


class OTPVerifyView(APIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = OTPVerifySerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        success, response_data, status_code = OTPService.verify_otp(email, otp, ip_address, user_agent)
        
        return Response(response_data, status=status_code)


class CustomUsersViewSet(UserViewSet):
    pagination_class = UserPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["is_active", "is_staff", "is_superuser", "username", "email"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["date_joined"]
    ordering = ["-date_joined"]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def list(self, request, *args, **kwargs):
        cache_key = f"user_list_{hash(str(request.query_params))}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.info("Cache hit for users list")
            return Response(cached_response)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=settings.CACHE_TIMEOUT)
        logger.info("Users list cached")
        return response
    
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        cache_key = f"user_detail_{user.id}"
        cached_response = cache.get(cache_key)
        
        if cached_response:
            logger.info(f"Cache hit for user detail - User: {user.id}")
            return Response(cached_response)

        serializer = self.get_serializer(user)
        cache.set(cache_key, serializer.data, timeout=settings.CACHE_TIMEOUT)
        logger.info(f"User detail cached - User: {user.id}")
        
        return Response(serializer.data)
