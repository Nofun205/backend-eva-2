from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AreaConocimiento, Curso, CarroMatricula, ItemCarro, MatriculaOrden, DetalleMatricula

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Roles y Permisos', {'fields': ('rol',)}),
    )
    list_display = ['username', 'email', 'rol', 'is_staff']
    search_fields = ['username', 'email']
    list_filter = ['rol', 'is_staff']

@admin.register(AreaConocimiento)
class AreaConocimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre', 'descripcion')

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    # CRUD avanzado: Permite editar precio y cupos directo desde la tabla
    list_display = ('titulo', 'area', 'costo_matricula', 'cupos_disponibles', 'fecha_inicio', 'fecha_termino')
    list_editable = ('costo_matricula', 'cupos_disponibles')
    list_filter = ('area', 'fecha_inicio')
    search_fields = ('titulo', 'descripcion')
    date_hierarchy = 'fecha_inicio'

class DetalleMatriculaInline(admin.TabularInline):
    model = DetalleMatricula
    extra = 0
    readonly_fields = ('curso', 'precio_congelado')

@admin.register(MatriculaOrden)
class MatriculaOrdenAdmin(admin.ModelAdmin):
    list_display = ('id', 'estudiante', 'estado', 'total_pagado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('estudiante__username',)
    list_editable = ('estado',)
    inlines = [DetalleMatriculaInline]
    date_hierarchy = 'fecha_creacion'

@admin.register(CarroMatricula)
class CarroMatriculaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'activo', 'creado_en')
    search_fields = ('estudiante__username',)

admin.site.register(ItemCarro)
admin.site.register(DetalleMatricula)
