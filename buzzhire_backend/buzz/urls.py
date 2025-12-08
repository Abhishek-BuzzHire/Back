from django.urls import path
from .views import PunchInView, PunchOutView, TodayAttendanceView
from .views import GoogleAuthView


urlpatterns = [
    path("google/", GoogleAuthView.as_view()),

    # Attendence
    path("punch-in/", PunchInView.as_view(), name="punch-in"),
    path("punch-out/", PunchOutView.as_view(), name="punch-out"),
    path("today/", TodayAttendanceView.as_view()),
]