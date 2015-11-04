from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from ct.core.models import Event
from .models import EventGuest
from .forms import UploadFileForm


######### HELPER FUNCTIONS ##########
def uploadRowToDict(fileobj):
	"""
	Helper Generator function. Unfortunately csv.DictReader doesn't play nice with djagno's
	uploaded file classes, so this acts as a parser.
	"""
	for row in fileobj:
		rowlist = row.decode('utf-8').split(',')
		returndict = {}
		for inx, x in enumerate(['pfx', 'first', 'last', 'plusOne', 'extends']):
			returndict[x] = rowlist[inx]
		yield returndict

####### REGULAR VIEWS #######
@user_passes_test(lambda x: x.is_superuser)
def loadEventWithGuests(request):
	"""
	Form that submits a CSV of guests to be loaded into an event.
	For a reference on the CSV file, see the html page this view renders on GET.

	Note that this is very pared down for convenience. Allows me to feed in a
	big list for the demo. A production version would have a lot more validity
	checks and helpful error handling.

	Locked down to superuser, because even in the demo, I don't want other people
	using this. (My database rows are limited in free tier!)
	"""
	if request.method == 'GET':
		return render(request, 'eventLoaderForm.html',
			context={'events': Event.objects.all()},)

	if request.method == 'POST':

		#Get stuff we'll need.
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			ev = get_object_or_404(Event, pk=form.cleaned_data['event'])
			guests = EventGuest.objects.filter(event=ev)
			NextInvite = EventGuest.nextFreeInvitation(ev)
			falseExtends = {'n', 'f', 'no', 'false', ''}
			csvFile = request.FILES['csvfile']
			for index, reader in enumerate(uploadRowToDict(csvFile)):
				#CSV headers aren't guests.
				if not (index==0 and 'first' in reader['first'].lower() and 'last' in reader['last'].lower()):
					if reader['extends'] in falseExtends:
						NextInvite += 1
					try:
						plusOne = int(reader['plusOne'])
					except ValueError:
						plusOne = 0
					guest = EventGuest(event=ev, status=0, invitation=NextInvite,
						pfx=reader['pfx'], first=reader['first'], last=reader['last'],
						plusOne=plusOne)
					guest.clean() # Does a bit of custom validation, see model.
					guest.save()
			return render(request, 'thanks.html')
		else:
			return render(request, 'fileParseError.html'), 500
