from django.urls import path, include
from rest_framework import routers

from tickets import views


router = routers.SimpleRouter(trailing_slash=False)
router.register('settings', views.SettingViewSet)
router.register('tariffs', views.TariffViewSet)
router.register('routes', views.RouteViewSet)
router.register('ticket-types', views.TicketTypeViewSet)
router.register('agents', views.AgentViewSet),
router.register('sellers', views.SellerViewSet)
router.register('carriers', views.CarrierViewSet)
router.register('inspectors', views.InspectorViewSet)
router.register('validators', views.ValidatorViewSet)
router.register('tickets', views.TicketViewSet)
router.register('operations', views.OperationViewSet)
router.register('workdays', views.WorkdayViewSet)
router.register('', views.AdminViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
