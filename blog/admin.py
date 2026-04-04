from django.contrib import admin
from .models import Post,Follow
from .models import Profile

admin.site.register(Post)
admin.site.register(Follow)
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_name", "city", "is_completed")

    def get_name(self, obj):
        return obj.user.get_full_name()