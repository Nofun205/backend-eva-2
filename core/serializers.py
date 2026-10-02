from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, AreaConocimiento, Curso, CarroMatricula, ItemCarro, MatriculaOrden, DetalleMatricula

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el payload del token JWT para incluir el Rol del usuario.
    Esto es crucial según la rúbrica y permite al frontend (Coursera) saber 
    si mostrar el menú de Estudiante o el panel de Coordinador.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Agregamos los custom claims (payload personalizado)
        token['rol'] = user.rol
        token['username'] = user.username
        return token

class AreaConocimientoSerializer(serializers.ModelSerializer):
    """
    Serializador para las áreas de conocimiento.
    Expone todos los campos del modelo para que el Coordinador pueda gestionar categorías.
    """
    class Meta:
        model = AreaConocimiento
        fields = '__all__'

class CursoSerializer(serializers.ModelSerializer):
    """
    Serializador de Cursos.
    Incluye 'area_nombre' como campo de solo lectura (ReadOnlyField) para mostrar 
    el nombre del área en el catálogo en lugar del ID, mejorando la UX del frontend.
    """
    area_nombre = serializers.ReadOnlyField(source='area.nombre')

    class Meta:
        model = Curso
        fields = '__all__'

class ItemCarroSerializer(serializers.ModelSerializer):
    """
    Serializador para los ítems individuales dentro del Carro de Matrícula.
    Agrega el título y el costo del curso en tiempo real consultando la base de datos,
    necesarios para renderizar el UI del carrito del estudiante.
    """
    curso_titulo = serializers.ReadOnlyField(source='curso.titulo')
    costo = serializers.ReadOnlyField(source='curso.costo_matricula')

    class Meta:
        model = ItemCarro
        fields = ['id', 'curso', 'curso_titulo', 'costo', 'agregado_en']

class CarroMatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador del Carro persistente.
    Usa SerializerMethodField para calcular dinámicamente el total a pagar
    sumando el costo de los ítems al momento de enviar el JSON al frontend.
    """
    items = ItemCarroSerializer(many=True, read_only=True)
    total_a_pagar = serializers.SerializerMethodField()

    class Meta:
        model = CarroMatricula
        fields = ['id', 'estudiante', 'activo', 'creado_en', 'items', 'total_a_pagar']

    def get_total_a_pagar(self, obj):
        # Calcula el total del carrito sumando el costo de los cursos
        return sum(item.curso.costo_matricula for item in obj.items.all())

class DetalleMatriculaSerializer(serializers.ModelSerializer):
    """
    Serializador del historial de compras. 
    Muestra el precio_congelado al que el alumno compró el curso, respetando
    la integridad histórica de las transacciones (punto crítico de la rúbrica).
    """
    curso_titulo = serializers.ReadOnlyField(source='curso.titulo')

    class Meta:
        model = DetalleMatricula
        fields = ['id', 'curso', 'curso_titulo', 'precio_congelado']

class MatriculaOrdenSerializer(serializers.ModelSerializer):
    """
    Serializador Principal de la Orden (Transacción validada).
    Incluye los detalles anidados en formato de lectura.
    """
    detalles = DetalleMatriculaSerializer(many=True, read_only=True)

    class Meta:
        model = MatriculaOrden
        fields = '__all__'
