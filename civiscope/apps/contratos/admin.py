from django.contrib import admin

from .models import Contrato


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_processo",
        "municipio",
        "empresa",
        "valor",
        "data_assinatura",
        "data_publicacao",
    )
    search_fields = ("numero_processo", "empresa__nome", "empresa__cnpj", "municipio__nome")
    list_filter = ("municipio__estado", "data_assinatura", "data_publicacao")
    autocomplete_fields = ("municipio", "empresa")
    date_hierarchy = "data_assinatura"
