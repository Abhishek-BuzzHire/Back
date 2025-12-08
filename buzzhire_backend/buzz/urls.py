from django.urls import path
from .views import PunchInView, PunchOutView, TodayAttendanceView
from .views import GoogleAuthView


urlpatterns = [
    path("google/", GoogleAuthView.as_view()),

    # Attendence
    path("api/attendance/punch-in/", PunchInView.as_view(), name="punch-in"),
    path("api/attendance/punch-out/", PunchOutView.as_view(), name="punch-out"),
    path("api/attendance/today/", TodayAttendanceView.as_view()),
]