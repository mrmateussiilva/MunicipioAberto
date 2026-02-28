from django.contrib import admin

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "data_abertura", "municipio")
    search_fields = ("nome", "cnpj")
    list_filter = ("municipio__estado",)
    autocomplete_fields = ("municipio",)
