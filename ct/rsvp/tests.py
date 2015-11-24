from django.test import TestCase, Client
from django.contrib.auth.models import User
import os
import datetime

from ct.core.models import Event

from .views import loadEventWithGuests
from .models import EventGuest
from .serializers import GuestFullSerializer, GuestPublicSerializer, InvitationPublicSerializer, InvitationFullSerializer
from .exceptions import MixedInvitationException

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
	
	def test_cleaner_handles_nonetype(self):
		a = EventGuest(pfx=None, first='mitchell ')
		a.clean()
		self.assertEqual(a.pfx, None)
		
	
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
		


class TestGuestSerializersFromPrimitives(TestCase):
	
	def setUp(self):
		self.ev = Event(name='Test Event', event_date=datetime.date.today())
		self.ev.save()
	
	def test_can_save_from_public_fields(self):
		a = {'invitation': 4, 'pfx': None, 'first': '  mitchell', 'last': 'stoutin ',
		'plusOne': 1, 'orderer': 0, 'event': self.ev.pk,}
		b = GuestPublicSerializer(data=a)
		self.assertTrue(b.is_valid())
		b.save() #should throw exception invalid at model level.
	
	def test_will_update_from_public_fields(self):
		a = {'invitation': 4, 'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
		'plusOne': 1, 'orderer': 0}
		b = EventGuest(event=self.ev, **a)
		b.save()
		a['first'] = 'Daylen'
		a['event'] = self.ev.pk
		c = GuestPublicSerializer(b, data=a)
		self.assertTrue(c.is_valid())
		c.save()
		self.assertEqual(b.first, 'Daylen')
		
	def test_names_and_pfxs_stripped_on_save(self):
		a = {'invitation': 4, 'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
		'plusOne': 1, 'orderer': 0, 'event': self.ev.pk, 'status':1}
		b = GuestFullSerializer(data=a)
		self.assertTrue(b.is_valid())
		instance = b.save()
		self.assertEqual(instance.pfx, 'Mr.')
		self.assertEqual(instance.first, 'mitchell')
		self.assertEqual(instance.last, 'stoutin')
		rightnum = instance.pk
		
		#If called with an ID, serializer.save() will call separate method,
		# update(). Test that update() also cleans names.
		c = {'invitation': 4, 'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
		'plusOne': 1, 'orderer': 0, 'event': self.ev.pk, 'status':1, 'id': instance.pk}
		d = GuestFullSerializer(instance, data=c)
		self.assertTrue(d.is_valid())
		instance = d.save()
		self.assertEqual(instance.pfx, 'Mr.')
		self.assertEqual(instance.first, 'mitchell')
		self.assertEqual(instance.last, 'stoutin')
		#make sure this test didn't just create a second EventGuest.
		self.assertEqual(instance.pk, rightnum)
	
		def test_invalid_without_event(self):
			a = {'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
			'plusOne': 0, 'orderer': 0, 'status':1}
			b = GuestFullSerializer(data=a) #lacks an event.
			self.assertFalse(b.is_valid())

			


class TestGuestSerializersFromPythonObjects(TestCase):
	
	def setUp(self):
		self.ev = Event(name='Test Event', event_date=datetime.date.today())
		self.ev.save()
		self.a = {'invitation': 4, 'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
		'plusOne': 1, 'orderer': 0, 'event': self.ev, 'status':1}
		self.b = EventGuest(**self.a)
		self.b.save()
	
	def test_guest_public_hides_attendance(self):
		c = GuestPublicSerializer(self.b)
		self.assertFalse('status' in c.data.keys())
		
	
	def test_invitation_public_hides_status(self):
		c = InvitationPublicSerializer(self.b)
		self.assertFalse('status' in c.data.keys())
		

	
class TestInvitationListSerializer(TestCase):
	
	def setUp(self):
		self.ev = Event(name='Test Event', event_date=datetime.date.today())
		self.ev.save()
		self.a = {'pfx': 'Mr', 'first': '  mitchell', 'last': 'stoutin ',
			'plusOne': 0, 'orderer': 0, 'status':1}
		self.b = {'pfx': 'Mrs', 'first': 'jaqueline', 'last': 'stoutin ',
			'plusOne': 1, 'orderer': 2, 'status':1}
		self.c = {'first': 'Nonexistent Baby', 'last': 'Stoutin', 'orderer': 3,
			'status': 2}
		
		
	#currently failing.
	def test_save_from_prim_puts_all_on_same_invite(self):
		abc = [self.a, self.b, self.c]
		for x in abc:
			x['event'] = self.ev.pk
		s = InvitationFullSerializer(data=abc, many=True)
		self.assertTrue(s.is_valid())
		s.save()
		qs = EventGuest.objects.filter(event=self.ev)
		self.assertEqual(qs.count(), 3)
		invitation = {l.invitation for l in qs}
		self.assertEqual(len(invitation), 1)
		