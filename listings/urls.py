from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact_view, name="contact"),
    path("auth/", views.auth_view, name="auth"),
    path("login/", views.auth_view, name="login"),  # Backward compatibility
    path("logout/", views.logout_view, name="logout"),
    path("signup/buyer/", views.auth_view, name="register_buyer"),  # Backward compatibility
    path("signup/seller/", views.auth_view, name="register_seller"),  # Backward compatibility
    path("dashboard/", views.dashboard, name="dashboard"),
    path("properties/add/", views.property_create, name="property_create"),
    path("properties/<int:property_id>/", views.property_detail, name="property_detail"),
    path("properties/<int:property_id>/inquiry/", views.property_inquiry, name="property_inquiry"),
    path("properties/<int:property_id>/toggle-sold/", views.toggle_sold, name="property_toggle_sold"),
    path("properties/<int:property_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("properties/<int:property_id>/edit/", views.property_update, name="property_update"),
    path("properties/<int:property_id>/delete/", views.property_delete, name="property_delete"),
]