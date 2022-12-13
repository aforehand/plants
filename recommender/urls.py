from django.urls import path

from . import views

urlpatterns = [
    path('', views.GuildRecommenderView.as_view(template_name="guild_recommender.html")),
]