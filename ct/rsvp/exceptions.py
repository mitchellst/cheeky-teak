class MixedInvitationError(Exception):
	"""
	Raised when the caller violates an expectation that all guest objects have
	same invitation number, or guest.invitation is None for all guests, or all
	guests are missing the key "invitation."
	"""
	pass
	
class NoEventError(Exception):
	"""
	Raised if/when a collection of guest objects is "orphaned," or passed to some
	process that requires the event that the guests are associated with, but the
	event is not passed in any form with them.
	"""
	pass