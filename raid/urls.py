from django.urls import path
from . import views
urlpatterns = [
    path('healthz/',views.healthcheck,name='healthcheck'),
    path('',views.home,name='home'),
    path('join/',views.join,name='join'),
    path('demo/reset/',views.reset_demo,name='reset_demo'),
    path('mission/<int:pk>/',views.question_detail,name='question'),
    path('mission/<int:pk>/check-line/',views.check_line,name='check_line'),
    path('mission/<int:pk>/submit/',views.submit_answer,name='submit'),
    path('results/',views.results,name='results'),
    path('results/export.csv',views.export_results,name='export_results'),
    path('api/status/',views.api_status,name='api_status'),
]
