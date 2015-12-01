import datetime
from django.test import TestCase, Client

from ct.core.models import Event

from ct.rsvp.models import EventGuest
from ct.rsvp.exceptions import MixedInvitationError, NoEventError


class TestEventGuestModel(TestCase):
	
	def test_nextFreeInvitation_method_raises_exception_on_noEvent(self):
		with self.assertRaises(NoEventError):
			EventGuest.nextFreeInvitation(None)
		
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
		