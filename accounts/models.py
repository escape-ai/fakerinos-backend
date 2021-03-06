from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from guardian.mixins import GuardianUserMixin
from django.conf import settings
from django.utils import timezone
from articles.models import Tag, Deck
from datetime import datetime, timedelta
import logging


class User(GuardianUserMixin, AbstractUser):
    pass


class Player(models.Model):
    user = models.OneToOneField(User, primary_key=True, editable=False, on_delete=models.CASCADE)
    room = models.ForeignKey('rooms.Room', on_delete=models.SET_NULL, related_name='players', editable=False, null=True)
    skill_rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1000)],
                                       default=500)
    rank = models.PositiveIntegerField(null=True, editable=False)
    finished_decks = models.ManyToManyField(Deck, related_name='finishers', editable=False, blank=True)
    starred_decks = models.ManyToManyField(Deck, related_name='starrers', blank=True)
    score = models.IntegerField(default=0)
    ready = models.BooleanField(default=False)
    game_score = models.IntegerField(default=0)

    def get_score(self, delta: timedelta = None):
        now = timezone.now()
        beginning_of_time = timezone.datetime.fromtimestamp(0)
        start_time = beginning_of_time if delta is None else now - delta
        logging.info(f"Getting scores starting from {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        games = self.games.all() if delta is None else self.games.filter(time__gte=start_time)
        return sum([game.player_scores[self.pk] for game in games])

    def __str__(self):
        return f"Player ({self.user})"


class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True, editable=False, on_delete=models.CASCADE)
    education = models.CharField(max_length=50, default="Unknown", blank=True)
    gender = models.CharField(max_length=50, default="Unknown", blank=True)
    birth_date = models.DateField(null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    interests = models.ManyToManyField(Tag, related_name='interested_users', blank=True)
    onboarded = models.BooleanField(default=False, blank=True)

    @property
    def is_complete(self):
        conditions = [
            self.education != "Unknown",
            len(self.interests.all()),
            self.birth_date is not None,
            self.gender != "Unknown",
            self.avatar is not None,
            (self.first_name or self.last_name),
        ]
        return all(conditions)

    @property
    def age(self):
        if self.birth_date is not None:
            return (timezone.now().date() - self.birth_date).days // 365

    def __str__(self):
        return f"Profile ({self.user})"


def get_anonymous_user_instance(user_model) -> User:
    """
    Used by Django-guardian during migrations.
    Should return a User instance
    """
    return user_model(username=settings.ANONYMOUS_USER_NAME, )
