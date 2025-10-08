"""
URLs principais do projeto.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/paympesa/', include('payments_mpesa.urls')),
    path('api/payemola/', include('payments_emola.urls')),

    
]