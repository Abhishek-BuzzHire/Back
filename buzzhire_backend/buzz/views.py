from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, date
from .models import Attendance
from .serializers import AttendanceSerializer
from .utils.distance_utils import calculate_distance
from .constants import BRANCHES, PUNCH_RADIUS
from rest_framework import status
from django.conf import settings
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework_simplejwt.tokens import RefreshToken
from google.auth.exceptions import InvalidValue

# Create your views here.

# FOR BRANCH DETECT...

User = get_user_model()

class GoogleAuthView(APIView):
    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"error": "id_token required"}, status=400)

        try:
            info = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=300
            )

            email = info.get("email")
            name = info.get("name", email)
            picture = info.get("picture")

            if email not in settings.WHITELISTED_EMAILS:
                return Response({"error": "Not allowed"}, status=403)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"name": name,
                          "picture": picture,
                          "lastlogin": datetime.now()}
            )

            if not created:
                user.name = name 
                user.picture = picture
                user.lastlogin = datetime.now()
                user.save()

            refresh = RefreshToken.for_user(user)
            refresh["email"] = user.email
            refresh["name"] = user.name
            refresh["picture"] = user.picture


            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "email": email,
                "name": name,
                "picture": picture,
                "user_id": user.pk,
            })

        except InvalidValue as e:
            print(f"Google Token Verification Failed: {e}") 
            return Response({"error": f"Invalid token (details: {e})"}, status=400)
        except Exception as e:
            print(f"Authentication Error: {e}")
            return Response({"error": "Invalid token (internal error)"}, status=400)


def detect_branch(user_lat, user_lon):
    """
    Returns (True, branch_name, distance) if inside any branch range.
    Else returns (False, None, None)
    """

    for branch in BRANCHES:
        dist = calculate_distance(
            user_lat, user_lon,
            branch["lat"], branch["lon"]
        )

        if dist <= PUNCH_RADIUS:
            return True, branch["name"], dist

    return False, None, None

class PunchInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 0️⃣ Validate input
        if "latitude" not in request.data or "longitude" not in request.data:
            return Response(
                {"status": "failed", "message": "latitude & longitude are required"},
                status=400
            )

        user_lat = float(request.data.get("latitude"))
        user_lon = float(request.data.get("longitude"))

        # 1️⃣ Check for today's attendance (latest record)
        today = date.today()
        attendance = Attendance.objects.filter(
            user=user,
            punch_in_time__date=today
        ).order_by('-id').first()  # get latest attendance record

        # 2️⃣ Find nearest branch
        nearest_branch = None
        nearest_distance = float("inf")
        for b in BRANCHES:
            dist = calculate_distance(user_lat, user_lon, b["lat"], b["lon"])
            if dist < nearest_distance:
                nearest_distance = dist
                nearest_branch = b

        # 2.1️⃣ Check if user is in range
        if nearest_distance > PUNCH_RADIUS:
            return Response({
                "status": "failed",
                "message": "You are out of range",
                "nearest_branch": nearest_branch["name"],
                "distance": round(nearest_distance, 2)
            }, status=400)

        # 3️⃣ Handle punch-in logic
        if attendance:
            if attendance.punch_out_time is None:
                # Already punched in
                return Response({
                    "status": "failed",
                    "message": "You are already punched in today",
                    "data": AttendanceSerializer(attendance).data
                }, status=400)
            else:
                # Punched out before, update with new punch-in
                attendance.punch_in_time = datetime.now()
                attendance.punch_in_lat = user_lat
                attendance.punch_in_lon = user_lon
                attendance.punch_out_time = None  # reset punch out
                attendance.punch_out_lat = None
                attendance.punch_out_lon = None
                attendance.save()
                message = "Punch in updated successfully"
        else:
            # No attendance today, create new record
            attendance = Attendance.objects.create(
                user=user,
                punch_in_time=datetime.now(),
                punch_in_lat=user_lat,
                punch_in_lon=user_lon
            )
            message = "Punch in successful"

        return Response({
            "status": "success",
            "message": message + f" at {nearest_branch['name']}",
            "branch": nearest_branch["name"],
            "distance": round(nearest_distance, 2),
            "data": AttendanceSerializer(attendance).data
        }, status=201)



class PunchOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 1️⃣ Validate inputs
        if "latitude" not in request.data or "longitude" not in request.data:
            return Response(
                {"status": "failed", "message": "latitude & longitude are required"},
                status=400
            )

        user_lat = float(request.data.get("latitude"))
        user_lon = float(request.data.get("longitude"))

        # 2️⃣ Find today’s active punch-in
        today = date.today()
        attendance = Attendance.objects.filter(
            user=user,
            punch_in_time__date=today,
            punch_out_time__isnull=True
        ).first()

        if not attendance:
            return Response({
                "status": "failed",
                "message": "You have not punched in today"
            }, status=400)

        # 3️⃣ Find nearest branch
        nearest_branch = None
        min_distance = float("inf")

        for branch in BRANCHES:
            dist = calculate_distance(user_lat, user_lon, branch["lat"], branch["lon"])
            if dist < min_distance:
                min_distance = dist
                nearest_branch = branch

        distance = min_distance

        # Range check
        if distance > PUNCH_RADIUS:
            return Response({
                "status": "failed",
                "message": f"You are out of range for {nearest_branch['name']}",
                "distance": round(distance, 2),
                "branch": nearest_branch["name"]
            }, status=400)

        # 4️⃣ Save punch-out
        attendance.punch_out_time = datetime.now()
        attendance.punch_out_lat = user_lat
        attendance.punch_out_lon = user_lon
        attendance.save()

        return Response({
            "status": "success",
            "message": f"Punch out successful",
            "branch": nearest_branch["name"],
            "distance": round(distance, 2),
            "data": AttendanceSerializer(attendance).data
        }, status=200)

class TodayAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        # Get latest attendance for today
        attendance = Attendance.objects.filter(
            user=user,
            punch_in_time__date=today
        ).order_by('-id').first()

        if not attendance:
            # User has not punched in today at all
            return Response({
                "status": "success",
                "data": {
                    "is_punched_in": False,
                    "has_punched_out": False,
                    "punch_in_time": None,
                    "punch_out_time": None,
                    "branch": None,
                    "distance": None
                }
            }, status=200)

        # Determine status flags
        is_punched_in = attendance.punch_in_time is not None
        has_punched_out = attendance.punch_out_time is not None

        return Response({
            "status": "success",
            "data": {
                "is_punched_in": is_punched_in and not has_punched_out,
                "has_punched_out": has_punched_out,
                "punch_in_time": attendance.punch_in_time,
                "punch_out_time": attendance.punch_out_time,
                "branch": getattr(attendance, "branch_name", None),  # optional, safe
                "distance": None,   # distance only calculated at punch time
                "raw": AttendanceSerializer(attendance).data
            }
        }, status=200)
