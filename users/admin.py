from django.contrib import admin
from users.models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

admin.site.register(User, UserAdmin)