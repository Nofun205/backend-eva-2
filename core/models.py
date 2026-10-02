from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

class User(AbstractUser):
    """
    Modelo de usuario personalizado.
    Implementa el rol para separar lógica de Estudiante vs Coordinador Académico.
    """
    ROLE_CHOICES = (
        ('ESTUDIANTE', 'Estudiante'),
        ('COORDINADOR', 'Coordinador Académico'),
    )
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ESTUDIANTE')

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"


class AreaConocimiento(models.Model):
    """
    Administrada por el Coordinador. Clasifica los cursos.
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Curso(models.Model):
    """
    Bootcamp o Curso disponible para inscripción.
    Contiene límite máximo de cupos y disponibilidad actual.
    """
    area = models.ForeignKey(AreaConocimiento, on_delete=models.CASCADE, related_name='cursos')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    costo_matricula = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField()
    cupos_maximos = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    cupos_disponibles = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Si es un curso nuevo, los cupos disponibles iniciales son iguales al límite máximo
        if not self.pk and self.cupos_disponibles is None:
            self.cupos_disponibles = self.cupos_maximos
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo


class CarroMatricula(models.Model):
    """
    Relación 1 a 1 entre el Usuario y su Carro activo.
    Mantiene la persistencia de los ítems aunque el usuario cierre sesión.
    """
    estudiante = models.OneToOneField(User, on_delete=models.CASCADE, related_name='carro')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Carro de {self.estudiante.username} (Activo: {self.activo})"


class ItemCarro(models.Model):
    """
    Cada curso agregado por el estudiante al carro.
    No permite agregar el mismo curso dos veces al mismo carro.
    """
    carro = models.ForeignKey(CarroMatricula, on_delete=models.CASCADE, related_name='items')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Esto asegura que un curso no se agregue 2 veces al mismo carro de compras
        unique_together = ('carro', 'curso')

    def __str__(self):
        return f"{self.curso.titulo} en carro de {self.carro.estudiante.username}"


class MatriculaOrden(models.Model):
    """
    Orden generada al hacer el checkout.
    El stock (cupos) se descuenta solo cuando el estado pasa a PAGADO.
    """
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('CANCELADO', 'Cancelado'),
    )
    estudiante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matriculas')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Orden #{self.id} - {self.estudiante.username} - {self.estado}"


class DetalleMatricula(models.Model):
    """
    Congela el precio del curso al momento de la inscripción histórica.
    """
    matricula = models.ForeignKey(MatriculaOrden, on_delete=models.CASCADE, related_name='detalles')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    precio_congelado = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle Orden #{self.matricula.id} - {self.curso.titulo}"
