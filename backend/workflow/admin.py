from django.contrib import admin

from .models import (
    AuditLog,
    Entity,
    Rule,
    SchemaField,
    SchemaVersion,
    State,
    Transition,
    UserProfile,
    Workflow,
)


admin.site.register(Workflow)
admin.site.register(State)
admin.site.register(Transition)
admin.site.register(Rule)
admin.site.register(SchemaVersion)
admin.site.register(SchemaField)
admin.site.register(Entity)
admin.site.register(AuditLog)
admin.site.register(UserProfile)
