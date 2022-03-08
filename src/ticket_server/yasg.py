from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path


schema_view = get_schema_view(
   openapi.Info(
      title="Ticket Server REST API",
      default_version='1.0.0',
      description="API for Ticket server",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="ivanperovsky@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
   path(r'api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path(r'api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path(r'api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')
]
