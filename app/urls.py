from django.urls import path, re_path
from app import views

urlpatterns = [
    # Matches any html file - to be used for gentella
    # Avoid using your .html in your resources.
    # Or create a separate django app.
    # re_path(r'^.*\.html', views.gentella_html, name='gentella'),

    # The home page
    path('', views.index, name='index'),
    path('search',views.search,name='search'),
    path('stock/<str:pk>',views.stock,name='stock'),
    path('get/ajax/tweets', views.loadtweets, name = "loadtweets"),
    path('get/ajax/news', views.loadnews, name = "loadnews"),
    path('get/ajax/reddit', views.loadreddit, name = "loadreddit"),
    path('get/ajax/stock', views.loadstock, name = "loadstock")
   
]
