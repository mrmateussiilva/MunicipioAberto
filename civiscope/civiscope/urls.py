"""Root URL configuration."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "civiscope Admin"
admin.site.site_title = "civiscope"
admin.site.index_title = "Gestão de dados públicos municipais"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("municipios/", include("apps.municipios.urls", namespace="municipios")),
    path("", RedirectView.as_view(url="/municipios/", permanent=False)),
]
