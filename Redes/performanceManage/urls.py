from django.urls import path
from django.conf.urls import url
from django.contrib import admin

from . import views


urlpatterns = [
	# url(r'^reportes/$', views.ReporteListView.as_view(), name='reportes'),
    url(r"^estadisticas/(?P<fecha>[^/]+)/(?P<ip>[^/]+)/(?P<tipo>[^/]+)/(?P<valor>[^/]+)/$", views.nueva_estadistica)
]