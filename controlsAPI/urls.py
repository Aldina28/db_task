from django.urls import path
from . import views

urlpatterns = [
    path("control_create/", views.ControlCreateAPI.as_view()),
    path("control_delete/", views.ControlDeleteAPI.as_view()),
    path("control_details/", views.AllControlDetailsAPI.as_view()),
    path("control_update/", views.ControlUpdateAPI.as_view()),
    path("controlsetreference_update/", views.ControlsetRefUpdateAPI.as_view()),
    path("controlsetreference_details/", views.AllControlsetRefDetailsAPI.as_view()),
    path("controlset_create/", views.ControlSetCreateAPI.as_view()),
    path("controlset_update/", views.ControlSetUpdateAPI.as_view()),
    path("controlset_delete/", views.ControlSetDeleteAPI.as_view()),
    path("controlset_details/", views.AllControlSetDetailsAPI.as_view()),
    path("controlhierarchies_update/", views.ControlHierarchyUpdateAPI.as_view()),
    path("controlhierarchies_details/",views.AllControlHierarchiesDetailsAPI.as_view()),
    path("controlhierarchies_controlsetdelete/", views.ControlHierarchyControlsetDeleteAPI.as_view())
    
]
