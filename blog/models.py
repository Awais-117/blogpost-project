from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=200)

    excerpt = models.CharField(
        max_length=300,
        blank=True
    )

    content = models.JSONField()

    featured_image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True
    )

    category = models.CharField(
        max_length=100,
        blank=True
    )
    views = models.PositiveIntegerField(default=0)

    is_featured = models.BooleanField(default=False)

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subtitle = models.CharField(max_length=160, blank=True)
    
    scheduled_at = models.DateTimeField(null=True, blank=True)

    def reading_time(self):
        text = ""
        for block in self.content.get("blocks", []):
            if block["type"] == "paragraph":
                text += block["data"].get("text", "") + " "

        words = len(text.split())
        minutes = max(1, words // 200)
        return minutes
    def __str__(self):
        return self.title
    
    


class Clap(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="claps")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return f"{self.user} clapped {self.post}"
    


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.post}"    
    
    
# def reading_time(self):
#     words = len(self.content.rendered.split())
#     minutes = words // 200
#     return max(1, minutes) 





# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
#     city = models.CharField(max_length=100)
#     study = models.CharField(max_length=100)
#     bio = models.TextField(blank=True)
#     is_completed = models.BooleanField(default=False)

#     def __str__(self):
#         return self.user.username

class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    city = models.CharField(max_length=100, blank=True)
    study = models.CharField(max_length=100, blank=True)

    bio = models.TextField(blank=True)

    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username





class Follow(models.Model):

    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_set"
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers_set"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_follow"
            )
        ]
    def save(self, *args, **kwargs):
        if self.follower == self.following:
            raise ValueError("User cannot follow themselves")
        super().save(*args, **kwargs) 

    
   
    def __str__(self):
        return f"{self.follower} follows {self.following}"
    