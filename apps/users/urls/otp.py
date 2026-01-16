from django.urls import path

from apps.users.views import OTPRequestView, OTPVerifyView

app_name = 'otp'

urlpatterns = [
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
]
