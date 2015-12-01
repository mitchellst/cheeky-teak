from rest_framework import serializers
from ct.rsvp.models import EventGuest
from ct.core.models import Event
from ct.rsvp.exceptions import MixedInvitationError, NoEventError

PUBLIC_FIELDS = ('id', 'event', 'invitation', 'pfx', 'first', 'last', 'plusOne', 'orderer')

class EventDisplayInfoSerializer(serializers.ModelSerializer):
	"""
	Each event has its own settings for how invitations should be displayed. This
	serializes them to send to javascript apps.
	"""
	class Meta:
		model = Event
		fields = ('prefix_primary_guests', 'prefix_with_guests', 
				'surname_with_guests', 'and_joiner', 'with_joiner')


class GuestFullSerializer(serializers.ModelSerializer):
	"""
	Serializer class for arbitrary groups of guests.
	
	If you want a group of guests from a particular invitation, use
	InvitationFullSerializer.
	"""
	def create(self, validated_data):
		instance = self.Meta.model(**validated_data)
		instance.clean()
		instance.save()
		return instance	
	
	def update(self, instance, validated_data):
		for x in validated_data.keys():
			if x not in {'pk', 'id'}:
				setattr(instance, x, validated_data[x])
		instance.clean()
		instance.save()
		return instance
	
	class Meta:
		model = EventGuest

class GuestPublicSerializer(GuestFullSerializer):
	"""
	Serializer class for arbitrary group of guests that does not leak
	attending status of guests. To be used on public RSVP apps.
	"""
	class Meta(GuestFullSerializer.Meta):
		fields = PUBLIC_FIELDS


class InvitationListSerializer(serializers.ListSerializer):
	"""
	A list serializer for lists of guests who all share the same invitation.
	
	List serializer is instantiated when one of the "child" serializers is 
	initialized and passed keyword arg many=True.
	
	An exception will be raised unless all the guests share the same invitation
	or lack an assigned invitation number. (In which case, they'll all be given 
	the same one.)
	
	At present, this is practically pseudo-code. It doesn't work.
	"""
	
	def validate_same_invitation(self, guestObjectsList, guestDictList=None):
		"""
		Makes sure this is the list serializer you want. If you want to serialize
		an arbitrary list of guests not on the same invitation, use a "guest" serializer,
		not an "invite" one.
		"""
		if len({guest.invitation for guest in guestObjectsList}) > 1:
			raise MixedInvitationError("Not all the guests serialized share same invitation.")
		if guestDictList is not None:
			if not (all('invitation' not in [item.keys() for item in guestDictList]) or
					len({item['invitation'] for item in guestDictList}) > 1):
				raise MixedInvitationError	
		
	
	def create(self, validated_data):
		guests = [EventGuest(**item) for item in validated_data]
		self.validate_same_invitation(guests)
		inviteNumber = EventGuest.nextFreeInvitation(guests[0].event if len(guests) > 0 else None)
		for guest in guests:
			guest.invitation = inviteNumber
		return EventGuest.objects.bulk_create(guests)
	
		
	def update(self, instance, validated_data):
		self.validate_same_invitation(instance, guestDictList=validated_data)
		guest_mapping = {guest.id: guest for guest in instance}
		data_mapping = {item['id']: item for item in validated_data}
		
		out = []
		for guest_id, data in data_mapping.items():
			existing_guest = guest_mapping.get(guest_id, None)
			if existing_guest is None:
				out.append(self.child.create(data))
			else:
				out.append(self.child.update(existing_guest, data))
		
		for guest_id, guest in guest_mapping.items():
			if guest_id not in data_mapping:
				guest.delete()
		
		return out
			

class InvitationFullSerializer(GuestFullSerializer):
	"""
	Serializer for guests who should all share the same invitation (group).
	To serialize an arbitrary array of guests, use GuestFullSerializer.
	"""
	@classmethod
	def many_init(cls, *args, **kwargs):
		"""
		Here's where we'll validate that all the invitations are the same,
		or assign them.
		
		When passing many=True with a data kwarg, we need to make sure the representations
		are not orphaned from their event. Representations must either each have a dict key
		"event" which corresponds to the integer primary key, or you must pass the event as
		a keyword argument to the serializer along with many=True.
		
		"""
		if 'data' in kwargs:
			
			#validate data is a list.
			data = kwargs.pop('data')
			assert type(data) == list, (
				'''Invitation Serializer with many=True and non-empty data
				expects a list in the data representation, not a dict or other
				type.'''
			)
			eventNumber = kwargs.pop('event', None)
			if eventNumber is None:
				try:
					eventNumber = data[0]['event']
				except KeyError:
					raise NoEventError(
						'''No event information associated with this list of guests.
						Try passing `event` keyword arg to the serializer or guest representations
						with event attributes'''
						)
			
			#build invitations list to analyze
			invitations = [obj.pop('invitation', None) for obj in data]
			for inx, val in enumerate(invitations):
				if type(val) == str: #some data cleaning for types.
					val = val.strip()
					if val == '':
						invitations[inx] = None
					else:
						try:
							intval = int(val)
							invitations[inx] = intval
						except ValueError:
							pass
					
			integerInvitations = [x for x in invitations if type(x)==int]
			
			if integerInvitations: #isn't epmty
				allsame = map(lambda x: x==integerInvitations[0], integerInvitations)
				if not all(allsame): 
					raise MixedInvitationError('All Numbered invitations must be same.')
				numberToAssign = integerInvitations[0]
			
			else: #usually means invitations == [None,]*len(data):
				numberToAssign = EventGuest.nextFreeInvitation(eventNumber)
			for representation in data:
				representation['invitation'] = numberToAssign
			
			# put our work back in the keyword args dict, which we'll use below.
			kwargs['data'] = data
			
		else:
			instance_queryset = [args[0],] if isinstance(args[0], EventGuest) else args[0] #per the serializer API.
			allsame = map(lambda x: x.invitation==instance_queryset[0].invitation, instance_queryset)
			if not all(allsame):
				raise MixedInvitationError
			
		# finally make the serializer, knowing the above is done.
		child = cls(*args, **kwargs)
		list_kwargs = {'child': child,}
		list_kwargs.update({
			key: value for key, value in kwargs.items()
			if key in serializers.LIST_SERIALIZER_KWARGS
		})
		return InvitationListSerializer(*args, **list_kwargs)
		
	
	class Meta:
		model = EventGuest


class InvitationPublicSerializer(InvitationFullSerializer):
	"""
	Exact copy of InvitationFullSerializer, except that it does not leak the attending
	status of guests. To be passed to public-facing RSVP apps.
	"""
	
	class Meta(InvitationFullSerializer.Meta):
		fields = PUBLIC_FIELDS