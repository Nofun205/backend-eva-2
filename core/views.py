from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, AreaConocimiento, Curso, CarroMatricula, ItemCarro, MatriculaOrden, DetalleMatricula
from .serializers import (
    CustomTokenObtainPairSerializer, AreaConocimientoSerializer, 
    CursoSerializer, CarroMatriculaSerializer, ItemCarroSerializer, 
    MatriculaOrdenSerializer
)
from .permissions import IsStudent, IsCoordinator


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista para retornar el JWT Token con los custom claims del rol"""
    serializer_class = CustomTokenObtainPairSerializer


class AreaConocimientoViewSet(viewsets.ModelViewSet):
    """
    Público: GET
    Coordinador: POST, PUT, DELETE
    """
    queryset = AreaConocimiento.objects.all()
    serializer_class = AreaConocimientoSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsCoordinator()]


class CursoViewSet(viewsets.ModelViewSet):
    """
    Público: GET (Explorar catálogo con filtros)
    Coordinador: POST, PUT, DELETE (Gestión del catálogo)
    """
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    
    # Implementación de django-filter y buscadores
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['area', 'costo_matricula']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_inicio', 'costo_matricula']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsCoordinator()]


class CarroMatriculaViewSet(viewsets.ViewSet):
    """
    Exclusivo para el ESTUDIANTE.
    Maneja el Carro persistente vinculado a su usuario.
    """
    permission_classes = [IsStudent]

    def list(self, request):
        """Obtiene el carro activo del estudiante o lo crea si no existe."""
        carro, created = CarroMatricula.objects.get_or_create(estudiante=request.user)
        serializer = CarroMatriculaSerializer(carro)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def agregar_curso(self, request):
        """Agrega un curso al carro, evitando duplicados."""
        carro, created = CarroMatricula.objects.get_or_create(estudiante=request.user)
        curso_id = request.data.get('curso_id')
        
        try:
            curso = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return Response({'error': 'Curso no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validamos duplicados
        if ItemCarro.objects.filter(carro=carro, curso=curso).exists():
            return Response({'error': 'El curso ya está en tu carro.'}, status=status.HTTP_400_BAD_REQUEST)
        
        ItemCarro.objects.create(carro=carro, curso=curso)
        return Response({'status': 'Curso agregado al carro exitosamente.'}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'])
    def remover_curso(self, request):
        """Elimina un curso específico del carro."""
        carro = CarroMatricula.objects.filter(estudiante=request.user).first()
        curso_id = request.data.get('curso_id')
        if carro and curso_id:
            ItemCarro.objects.filter(carro=carro, curso_id=curso_id).delete()
        return Response({'status': 'Curso removido.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def vaciar(self, request):
        """Vacía el carrito completo"""
        carro, created = CarroMatricula.objects.get_or_create(estudiante=request.user)
        carro.items.all().delete()
        return Response({'status': 'Carro vaciado.'}, status=status.HTTP_204_NO_CONTENT)


class MatriculaOrdenViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin, viewsets.mixins.RetrieveModelMixin):
    """
    Maneja las inscripciones históricas de los Estudiantes.
    El coordinador puede actualizar los estados (ej. CANCELADO).
    """
    serializer_class = MatriculaOrdenSerializer
    
    def get_queryset(self):
        # El estudiante ve sus propias órdenes, el coordinador ve todas
        if getattr(self.request.user, 'rol', None) == 'COORDINADOR':
            return MatriculaOrden.objects.all()
        return MatriculaOrden.objects.filter(estudiante=self.request.user)

    def get_permissions(self):
        if self.action in ['cambiar_estado']:
            return [IsCoordinator()]
        return [permissions.IsAuthenticated()]
        
    @action(detail=True, methods=['patch'], permission_classes=[IsCoordinator])
    def cambiar_estado(self, request, pk=None):
        """El coordinador puede cambiar el estado. Si es CANCELADO devuelve cupos."""
        orden = self.get_object()
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado not in dict(MatriculaOrden.ESTADO_CHOICES):
            return Response({'error': 'Estado no válido'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Lógica de reposición automática de stock
        if nuevo_estado == 'CANCELADO' and orden.estado != 'CANCELADO':
            with transaction.atomic():
                for detalle in orden.detalles.all():
                    curso = detalle.curso
                    curso.cupos_disponibles += 1
                    curso.save()
                orden.estado = 'CANCELADO'
                orden.save()
            return Response({'status': 'Orden cancelada y cupos reestablecidos.'})
            
        orden.estado = nuevo_estado
        orden.save()
        return Response({'status': 'Estado actualizado', 'estado': nuevo_estado})


@api_view(['POST'])
@permission_classes([IsStudent])
def checkout_confirmar_matricula(request):
    """
    ENDPOINT CORE DE LA RÚBRICA.
    Transacción Atómica: Convierte el Carrito en una Orden PAGADA.
    """
    carro = CarroMatricula.objects.filter(estudiante=request.user).first()
    
    if not carro or not carro.items.exists():
        return Response({'error': 'El carro está vacío.'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Transacción Atómica
        with transaction.atomic():
            total_pagar = 0
            items_carro = carro.items.all()
            
            # 1. Verificación estricta de cupos con bloqueo de base de datos (select_for_update)
            for item in items_carro:
                curso = Curso.objects.select_for_update().get(id=item.curso.id)
                if curso.cupos_disponibles < 1:
                    raise Exception(f'El curso "{curso.titulo}" se quedó sin cupos.')
                total_pagar += curso.costo_matricula
                
            # 2. Crear la Orden (Transacción validada)
            orden = MatriculaOrden.objects.create(
                estudiante=request.user,
                estado='PAGADO', 
                total_pagado=total_pagar
            )
            
            # 3. Descontar stock y guardar detalle histórico congelando el precio
            for item in items_carro:
                curso = Curso.objects.get(id=item.curso.id)
                curso.cupos_disponibles -= 1
                curso.save()
                
                DetalleMatricula.objects.create(
                    matricula=orden,
                    curso=curso,
                    precio_congelado=curso.costo_matricula
                )
                
            # 4. Vaciar el carro (relación OneToOne persistente)
            carro.items.all().delete()
            
        return Response({
            'status': 'Checkout exitoso. Inscripción confirmada.',
            'orden_id': orden.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        # Si los cupos fallaron, hace Rollback automático de todo
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
