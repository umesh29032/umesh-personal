"""learning.urls — every page is a real, shareable, Ctrl+click-able URL.

    /learn/                      all courses
    /learn/interview/            interview prep, harvested from every chapter
    /learn/<course>/             one course's chapter list
    /learn/<course>/<chapter>/   one chapter
"""
from django.urls import path

from learning import views

app_name = 'learning'

urlpatterns = [
    path('', views.CourseIndexView.as_view(), name='index'),
    path('interview/', views.InterviewPrepView.as_view(), name='interview'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('revise/<slug:page>/', views.RevisionView.as_view(), name='revision'),
    path('<slug:course>/', views.CourseDetailView.as_view(), name='course'),
    path('<slug:course>/<slug:chapter>/', views.ChapterView.as_view(), name='chapter'),
    # user-state endpoints (POST only) — kept separate so content pages stay GET-only
    path('<slug:course>/<slug:chapter>/complete/',
         views.ToggleCompleteView.as_view(), name='toggle-complete'),
    path('<slug:course>/<slug:chapter>/bookmark/',
         views.ToggleBookmarkView.as_view(), name='toggle-bookmark'),
    path('<slug:course>/<slug:chapter>/beat/',
         views.HeartbeatView.as_view(), name='heartbeat'),
]
