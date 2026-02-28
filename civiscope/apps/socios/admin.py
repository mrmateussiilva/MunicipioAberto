from django.contrib import admin

from .models import Socio


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "cpf", "percentual_participacao")
    search_fields = ("nome", "cpf", "empresa__nome", "empresa__cnpj")
    list_filter = ("empresa__municipio__estado",)
    autocomplete_fields = ("empresa",)
