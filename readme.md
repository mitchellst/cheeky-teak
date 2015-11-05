#Cheeky Teak: An RSVP System
Cheeky Teak is a portfolio project that is meant to model an online RSVP system for weddings and other events. It consists in (or, will consist in) a few pieces:

* A single-page app where guests live-search a list of names to find their invitation, and specify whether they will be attending. This application is built in AngularJS. This would reside on the public wedding web site.
* A single-page app where event coordinators / brides can see the responses, and perform CRUD operations on the guest list. This application is built with Backbone.js.
* A REST API that links the single-page apps to the backend, built using the Django REST Framework.
* A restricted admin area. This part will not be accessible in the public demo because allowing guests to create events and guests in bulk would probably overload my database. (I'm trying to stay within free tier, here.) So, in place of an "onboarding" system where users can sign up and make their own events, I'm using the django admin site to stand up a single event that will work as my live sample. (Though, the code is set up to run as many events as you'd like.)

Since the javascript apps should be able to be served as static sites off a separate domain (thereby giving wedding web sites the ability to have "custom domains") it made sense to put them in a [separate repository.](https://github.com/mitchellst/cheekyteak-js)


#Necessary Environment Variables
`DJSECRETKEY` The secret key django will use.
