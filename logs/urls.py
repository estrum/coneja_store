from django.urls import path
from logs.views import LogListView

urlpatterns = [
    path('search/', 
         LogListView.as_view(), name='log-search'),
]
