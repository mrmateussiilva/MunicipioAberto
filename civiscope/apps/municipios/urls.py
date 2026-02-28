"""URL patterns for the municipios app."""

from __future__ import annotations

from django.urls import path

from . import views

app_name = "municipios"

urlpatterns = [
    path("", views.busca, name="busca"),
    path("<str:codigo_ibge>/", views.detalhe_municipio, name="detalhe"),
]
