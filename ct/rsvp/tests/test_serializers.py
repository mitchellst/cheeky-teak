from django.test import TestCase, Client
import datetime

from ct.core.models import Event
from ct.rsvp.models import EventGuest
from ct.rsvp.exceptions import MixedInvitationError, NoEventError

from ct.rsvp.serializers import (GuestFullSerializer, GuestPublicSerializer, 
	InvitationPublicSerializer, InvitationFullSerializer, InvitationListSerializer)



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
		
	def test_invitation_serializer_makes_invitationList(self):
		a = InvitationFullSerializer(data=[self.a, self.b, self.c], event=self.ev, many=True)
		
		#Note that you can pass event by object, as above, or by primary key:
		b = InvitationPublicSerializer(data=[self.a, self.b, self.c], event=self.ev.pk, many=True)
		self.assertIsInstance(a, InvitationListSerializer)
		self.assertIsInstance(b, InvitationListSerializer)
	

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
		