from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
import csv

from ct.core.models import Event
from .models import EventGuest


@user_passes_test(lambda x: x.is_superuser)
def loadEventWithGuests(request):
	"""
	Form that submits a CSV of guests to be loaded into an event.
	CSV Headers in, in order: Prefix, First, Last, Plus Ones, Extends.

	Plus Ones: Number of guests this person is authorized to bring.

	Extends: is this guest in the same group as the row above?
	Extends will be False for empty string, 'n'/'no'/'f'/'false'
	(case insensitive.) Any other value in box will mean yes, same group.

	Note that this is very pared down for convenience. Allows me to feed in a
	big list for the demo. A production version would have a lot more validity
	checks and helpful error handling.

	Locked down to superuser, because even in the demo, I don't want other people
	using this. (My database rows are limited in free tier!)
	"""
	if request.method == 'GET':
		return render(request, 'eventLoaderForm.html')
	if request.method == 'POST':

		#Get stuff we'll need.
		ev = get_object_or_404(Event, pk=int(request.POST['event']))
		guests = EventGuest.objects.filter(event=ev)
		NextInvite = 1 + max(guests, default=0, key=lambda guest: guest.invitation)
		falseExtends = {'n', 'f', 'no', 'false', ''}
		
		#Parse the file.
		if request.FILES['csvfile']:
			with open(request.FILES['csvfile']) as csvFile:
				reader = csv.DictReader(csvFile, fieldnames=('pfx', 'first', 'last', 'plusOne', 'extends'))
				for index, row in enumerate(reader):
					#CSV headers aren't guests.
					if index==0 and 'first' in row['first'].lower() and 'last' in row['last'].lower(): 
						pass
					#Everybody else is.
					else:
						if row['extends'] in falseExtends:
							NextInvite += 1
						try:
							plusOne = int(row['plusOne'])
						except ValueError:
							plusOne = 0
						guest = EventGuest(event=ev, status=0, invitation=NextInvite, 
							pfx=row['pfx'], first=row['first'], last=row['last'],
							plusOne=plusOne)
						guest.clean() # Does a bit of custom validation, see model.
						guest.save()
			return render(request, 'thanks.html')
		else:
			return render(request, 'fileParseError.html'), 500	



	