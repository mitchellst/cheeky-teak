from django.db import models
from django.contrib.auth.models import User

class Event(models.Model):
	RSVP_METHOD_CHOICES = (
		(0, 'Live Search'),
		(1, 'Code'),
		(2, 'Custom URL'),
	)
	name = models.CharField(max_length=60)
	event_date = models.DateField()
	prefix_primary_guests = models.BooleanField(default = True)
	prefix_with_guests = models.BooleanField(default=False)
	surname_with_guests = models.BooleanField(default=True)
	and_joiner = models.CharField(max_length=25, default = "&")
	with_joiner = models.CharField(max_length=25, default= "with")
	site_url = models.CharField(max_length=90, default="cheekyteak.com")
	rsvp_method = models.IntegerField(default=0)

	def __str__(self):
		return self.name


class Profile(models.Model):
	""" User Profile for CheekyTeak users.
		Accessible in views as request.user.profile.

		user_type options:
		0 = single event user, login forwards straight to event dashboard.
		1 = event planner, read access to multiple events.
		2 = CheekyTeak staff member, write access to all events.
	"""
	user = models.OneToOneField(User, primary_key=True, related_name='ctprofile')
	user_type = models.SmallIntegerField(default=0)
	following_events = models.CommaSeparatedIntegerField(max_length=200)
