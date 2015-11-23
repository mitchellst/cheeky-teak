from django.test import TestCase, Client
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
		User.objects.create_superuser('tester', 'test@testing.com', 'testme')
		self.c = Client()
		self.c.login(username='tester', password='testme')
		with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testfiles/test1.csv')) as f:
			self.response = self.c.post('/uploadGuests/', {'event': self.ev.pk, 'csvfile': f})


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
		User.objects.create_superuser('tester', 'test@testing.com', 'testme')
		self.c = Client()
		self.c.login(username='tester', password='testme')
		with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testfiles/test1.csv')) as f:
			self.response = self.c.post('/uploadGuests/', {'event': self.ev.pk, 'csvfile': f})

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

class TestEventGuestModel(TestCase):
	
	def test_nextFreeInvitation_method_fails_gracefully_on_None(self):
		a = EventGuest.nextFreeInvitation(None) #exception would error out test.
		self.assertIsInstance(a, int)
		
	def test_names_and_pfxs_stripped_on_clean(self):
		a = EventGuest(pfx='mr. ', first='mitchell ', last=' stoutin')
		a.clean()
		self.assertEqual(a.pfx, 'mr.')
		self.assertEqual(a.first, 'mitchell')
		self.assertEqual(a.last, 'stoutin')
	
	def test_appropriate_prefixes_receive_dot_on_clean(self):
		for x in ['mr', 'Mrs', 'Ms', 'Dr', 'mdm']:
			a = EventGuest(pfx=x, first='FirstName', last='Last Name')
			a.clean()
			self.assertEqual(a.pfx[-1], '.')
		a.pfx = 'Miss' #make sure it doesn't dot everything.
		a.clean()
		self.assertNotEqual(a.pfx[-1], '.')
	
	def test_nextFreeInvite_incriments(self):
		ev = Event(name='Test Event', event_date=datetime.date.today())
		ev.save()
		defaults = {'event': ev, 'first': 'FirstName', 'last': 'Last Name'}
		latest = 0
		for x in range(10):
			guest = EventGuest(invitation=EventGuest.nextFreeInvitation(ev), **defaults)
			guest.save()
			self.assertTrue(guest.invitation > latest)
			latest = guest.invitation
		


class TestSerializersFromPrimitives(TestCase):
	
	def can_save_from_public_fields(self):
		pass
		
	def test_names_and_pfxs_stripped_on_save(self):
		pass
	


class TestSerializersFromPythonObjects(TestCase):
	
	def test_only_public_fields_from_guest_public(self):
		pass
	
	def test_only_public_fields_from_invitation_public(self):
		pass
	
	def test_event_info_only_public(self):
		pass
	
	