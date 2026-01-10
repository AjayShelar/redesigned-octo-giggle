from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AuditLogViewSet,
    EntityViewSet,
    RuleViewSet,
    SchemaFieldViewSet,
    SchemaVersionViewSet,
    StateViewSet,
    TransitionViewSet,
    UserProfileViewSet,
    WorkflowViewSet,
)

router = DefaultRouter()
router.register(r"workflows", WorkflowViewSet)
router.register(r"states", StateViewSet)
router.register(r"transitions", TransitionViewSet)
router.register(r"rules", RuleViewSet)
router.register(r"schema-versions", SchemaVersionViewSet)
router.register(r"schema-fields", SchemaFieldViewSet)
router.register(r"entities", EntityViewSet)
router.register(r"audit-logs", AuditLogViewSet)
router.register(r"user-profiles", UserProfileViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
