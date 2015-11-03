from django.db import models
from ct.core.models import Event as ctEvent

class EventGuest(models.Model):


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
		self.pfx.strip()
		if self.pfx.lower() in {'mr', 'mrs', 'ms', 'dr', 'mdm'}: #Zoom!Sets are speedy!
			self.pfx += '.'

	class Meta:
		ordering = ('invitation', 'orderer')
		"""
		Ordering like this isn't a free operation. Can bottleneck performance, but
		keeps you sane and this app is modest sized anyway.
		"""

