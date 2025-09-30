from django.urls import path
from . import views



urlpatterns = [
    path('login/', views.login_view, name='login'), 
    path('otp/', views.otp_view, name='otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('emp/', views.employee_info_view, name='emp'),
    path('generate-selected-id-cards/', views.generate_selected_id_cards, name='generate-selected-id-cards'),
    path('fetch_employee_data/', views.fetch_employee_data,name='fetch_employee_data')
    # path('otp/', views.otp_view, name='otp'), 
]
