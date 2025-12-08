from rest_framework import serializers

from .models import Attendance, User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # Call the base method to get the token object (includes user_id, email)
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.name # <-- Add the name
        token['email'] = user.email # <-- Add the email (if not added by default)
        token['email'] = user.picture

        return token


# =====================================================
# EMPLOYEE SELF PROFILE
# =====================================================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"



# =====================================================
# ATTENDANCE SERIALIZER
# =====================================================

# class AttendanceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Attendance
#         fields = "__all__"






class AttendanceSerializer(serializers.ModelSerializer):
    punch_in_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    punch_out_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False)

    date = serializers.DateField(read_only=True)  # <-- Must be read_only


    class Meta:
        model = Attendance
        fields = "__all__"
