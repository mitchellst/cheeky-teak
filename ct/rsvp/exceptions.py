class MixedInvitationException(Exception):
	"""
	Raised when the caller violates an expectation that all guest objects have
	same invitation number, or guest.invitation is None for all guests, or all
	guests are missing the key "invitation."
	"""
	pass