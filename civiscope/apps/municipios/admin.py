from django.contrib import admin

from .models import Municipio


@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ("nome", "estado", "codigo_ibge", "populacao", "data_criacao")
    search_fields = ("nome", "codigo_ibge")
    list_filter = ("estado",)
    ordering = ("estado", "nome")
