from django.test import TestCase
from django.http import HttpRequest
from django.contrib.auth.models import User
import os
import datetime

from ct.core.models import Event

from .views import loadEventWithGuests
from .models import EventGuest

class TestFileUploadOnFile1(TestCase):

	def setUp(self):
		self.ev = Event(name='Test Event', event_date=datetime.date.today())
		self.ev.save()
		self.request = HttpRequest()
		self.request.method = 'POST'
		self.request.user = User(is_superuser=True) #Get past that user test decorator.
		self.request.POST['event'] = str(self.ev.pk)
		self.request.FILES = {'csvfile': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testfiles/test1.csv')}
		self.response = loadEventWithGuests(self.request)

	def tearDown(self):
		EventGuest.objects.filter(event=self.ev).delete()
		self.ev.delete()

	def testFileUploadNoError(self):
		self.assertEqual(self.response.status_code, 200)	
	
	def testFileUploadMakesRightNumberOfGuests(self):
		qs = EventGuest.objects.filter(event=self.ev)
		self.assertEqual(qs.count(), 8)

	def testFileUploadMakesRightNumberOfInvitations(self):
		qs = EventGuest.objects.filter(event=self.ev)
		invites = set() #takes care of uniqueness.
		for guest in qs:
			invites.add(guest.invitation)
		self.assertEqual(len(invites), 6)

	def testFileUploadGroupsInvitationsProperly(self):
		for group in ['Stoutin', 'McCarthy']: #See test file.
			qs = EventGuest.objects.filter(event=self.ev, last=group)
			invite = qs[0].invitation
			for guest in qs:
				self.assertEqual(guest.invitation, invite)


class TestFileUploadOnFile2(TestCase):
	"""
	Same thing as test case 1, but tests on test file 2, which has no CSV headers.
	"""

	def setUp(self):
		self.ev = Event(name='Test Event', event_date=datetime.date.today())
		self.ev.save()
		self.request = HttpRequest()
		self.request.method = 'POST'
		self.request.user = User(is_superuser=True)
		self.request.POST['event'] = str(self.ev.pk)
		self.request.FILES = {'csvfile': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testfiles/test2.csv')}
		self.response = loadEventWithGuests(self.request)

	def tearDown(self):
		self.ev.delete()

	def testFileUploadNoError(self):
		self.assertEqual(self.response.status_code, 200)	
	
	def testFileUploadMakesRightNumberOfGuests(self):
		qs = EventGuest.objects.filter(event=self.ev)
		self.assertEqual(qs.count(), 8)

	def testFileUploadMakesRightNumberOfInvitations(self):
		qs = EventGuest.objects.filter(event=self.ev)
		invites = set() #takes care of uniqueness.
		for guest in qs:
			invites.add(guest.invitation)
		self.assertEqual(len(invites), 6)

	def testFileUploadGroupsInvitationsProperly(self):
		for group in ['Stoutin', 'McCarthy']: #See test file.
			qs = EventGuest.objects.filter(event=self.ev, last=group)
			invite = qs[0].invitation
			for guest in qs:
				self.assertEqual(guest.invitation, invite)

	def testDotPrefixesGetCorrected(self):
		self.assertEqual(EventGuest.objects.filter(event=self.ev, pfx='Mrs').count(), 0)
		self.assertEqual(EventGuest.objects.filter(event=self.ev, pfx='Mrs.').count(), 2)
		self.assertEqual(EventGuest.objects.filter(event=self.ev, pfx='Miss').count(), 1)