from django.contrib import admin

from .models import Indicador


@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ("tipo", "contrato", "score", "data_calculo")
    search_fields = ("tipo", "descricao", "contrato__numero_processo")
    list_filter = ("tipo", "data_calculo")
    autocomplete_fields = ("contrato",)
    readonly_fields = ("data_calculo",)
