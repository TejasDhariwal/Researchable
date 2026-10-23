from django.urls import path
from .views import *

urlpatterns = [
    path('', home_page, name='home_page'),
    path('get-started/', research_questionnaire, name='research_questionnaire'),
    path('research_output', research_output, name='research_output'),
    path('download_presentation', download_presentation, name="download_presentation")
]