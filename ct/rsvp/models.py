from django.db import models
from ct.core.models import Event as ctEvent

class EventGuest(models.Model):
	"""
	Guest who is invited to an event. The only potentially confusing part of this
	is the "invitation" on each guest, which is an integer representing a group
	of EventGuest's invited to a given Event. See class method nextFreeInvitation
	for details.
	"""

	STATUS_CHOICES = ((0, 'Not Responded'),
						(1, 'Attending'),
						(2, 'Not Attending'),
						)
	status = models.IntegerField(choices=STATUS_CHOICES, default=0)
	event = models.ForeignKey(ctEvent)
	invitation = models.IntegerField() # For grouping guests together.
	pfx = models.CharField(max_length=7, null=True, blank=True)
	first = models.CharField(max_length=50)
	last = models.CharField(max_length=50, null=True, blank=True)
	plusOne = models.IntegerField(default=0)
	orderer = models.IntegerField(default=0)


	def clean(self):
		"""
		Only custom cleaning we need to do is make sure that prefixes have
		dots at the end if they need them. (E.g. 'Mr' becomes 'Mr.' but 'Miss'
		doesn't become 'Miss.') Framework handles the rest.
		"""
		self.pfx = self.pfx.strip()
		self.first = self.first.strip()
		self.last = self.last.strip()
		if self.pfx.lower() in {'mr', 'mrs', 'ms', 'dr', 'mdm'}: #Zoom!Sets are speedy!
			self.pfx += '.'


	@classmethod
	def nextFreeInvitation(cls, ev):
		"""
		Invitations are groups of guests, as in a foreign key relationship, except
		an actual foreign key would be redundant and wasteful in this case. This
		method accepts an instance of ct.core.models.Event and returns the number
		of the next "empty" group.
		"""
		guests = cls.objects.filter(event=ev)
		topInvite = max(guests, default=0, key=lambda guest: guest.invitation)
		if isinstance(topInvite, cls):
			return 1 + topInvite.invitation
		return 1


	class Meta:
		ordering = ('invitation', 'orderer')
		"""
		Ordering like this isn't a free operation. Can bottleneck performance, but
		keeps you sane and this app is modest sized anyway.
		"""
