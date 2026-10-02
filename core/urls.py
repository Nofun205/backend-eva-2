from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView,
    AreaConocimientoViewSet,
    CursoViewSet,
    CarroMatriculaViewSet,
    MatriculaOrdenViewSet,
    checkout_confirmar_matricula
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'areas', AreaConocimientoViewSet, basename='areas')
router.register(r'cursos', CursoViewSet, basename='cursos')
router.register(r'carro-matricula', CarroMatriculaViewSet, basename='carro-matricula')
# Ojo: la vista sirve tanto para el estudiante como para el admin, lo manejamos bajo la misma ruta
router.register(r'mis-matriculas', MatriculaOrdenViewSet, basename='mis-matriculas')

urlpatterns = [
    # Auth JWT
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom Checkout Endpoint
    path('matriculas/confirmar/', checkout_confirmar_matricula, name='checkout-confirmar'),
    
    # Endpoints generados por el router
    path('', include(router.urls)),
]
