from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import signup_view, complete_profile
urlpatterns = [
    path('', views.landing, name = 'landing'),
    path('home/', views.home, name='home'),
    path('post/<int:id>/', views.detail, name='detail'),
    path('post/<int:id>/clap/', views.toggle_clap, name='toggle_clap'),
    path('post/<int:id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:id>/delete/', views.delete_comment, name='delete_comment'),
    path('create/', views.create, name='create'),
    path('post/<int:id>/edit/', views.update, name='update'),
    path('post/<int:id>/delete',views.delete, name='delete'),
    path('signup/', signup_view, name = 'signup'),
    path("profile/complete/", complete_profile, name="complete_profile"),
    path("upload-inline-image/", views.upload_inline_image, name="upload_inline_image"),
    path('preview/<int:id>', views.preview, name='preview'),
    path('publish/<int:id>/', views.publish_final, name='publish_final'),
    path('schedule/<int:id>/', views.schedule_post, name='schedule_post'),
    path("cancel-schedule/<int:id>/", views.cancel_schedule, name="cancel_schedule"),
    path("profile/", views.profile_detail, name="profile_detail"),
    path("stories/", views.stories, name="stories"),
    path("library/", views.library, name="library"),
    path("stats/", views.stats, name="stats"),
    path("profile/<int:id>/", views.public_profile, name="public_profile"),
    path("profile<int:id>/follow/", views.toggle_follow, name="toggle_follow"),
    path("profile/<int:id>/followers/", views.followers_list, name="followers_list"),
    path("profile/<int:id>/following/", views.following_list, name="following_list"),
]