from django.contrib import admin
from django.urls import path
from home import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.home,name="index"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('signup/', views.signup, name="signup"),
    path('campaign/', views.campaign, name="campaign"),
    path('home/', views.main_home, name="home"),
    path('joinus/', views.joinus, name="joinus"),
    path('register_ngo/', views.register_ngo, name='register_ngo'),
    path('ngo_dashboard/', views.ngo_dash, name='ngo_dashboard'),
    path('ngo_details/', views.profile, name='ngo_details'),
    path('ngo_profile/', views.ngo_profile, name='ngo_profile'),
    path('userprofile/', views.user_profile, name='userprofile'),
    path('create_donation/', views.create_donation, name='create_donation'),
    path('create_campaign/', views.create_campaign, name='create_campaign'),
    path('ngo_donations/<int:ngo_id>/<int:don_id>/', views.ngo_donations, name='ngo_donations'),
    path('user_donation/<int:user_id>/<int:product_id>/', views.user_donation, name='user_donation'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

