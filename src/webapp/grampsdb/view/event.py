# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009         Douglas S. Blank <doug.blank@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# $Id: utils.py 19637 2012-05-24 17:22:14Z dsblank $
#

""" Views for Person, Name, and Surname """

## Gramps Modules
from webapp.utils import _, boolean, update_last_changed, build_search
from webapp.grampsdb.models import Event
from webapp.grampsdb.forms import *
from webapp.libdjango import DjangoInterface
from webapp.dbdjango import DbDjango
from gen.datehandler import displayer, parser

## Django Modules
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import Context, RequestContext

## Globals
dji = DjangoInterface()
db = DbDjango()
dd = displayer.display
dp = parser.parse

def process_event(request, context, handle, act, add_to=None): # view, edit, save
    """
    Process act on person. Can return a redirect.
    """
    context["tview"] = _("Event")
    context["tviews"] = _("Events")
    context["action"] = "view"
    view_template = "view_event_detail.html"

    if handle == "add":
        act = "add"
    if request.POST.has_key("action"):
        act = request.POST.get("action")

    # Handle: edit, view, add, create, save, delete, share, save-share
    if act == "share":
        item, handle = add_to
        context["pickform"] = PickForm("Pick event", 
                                       Event, 
                                       (),
                                       request.POST)     
        context["object_handle"] = handle
        context["object_type"] = item
        return render_to_response("pick.html", context)
    elif act == "save-share":
        item, handle = add_to 
        pickform = PickForm("Pick event", 
                            Event, 
                            (),
                            request.POST)
        if pickform.data["picklist"]:
            parent_model = dji.get_model(item) # what model?
            parent_obj = parent_model.objects.get(handle=handle) # to add
            ref_handle = pickform.data["picklist"]
            ref_obj = Event.objects.get(handle=ref_handle) 
            dji.add_event_ref_default(parent_obj, ref_obj)
            dji.rebuild_cache(parent_obj) # rebuild cache
            return redirect("/%s/%s%s#tab-events" % (item, handle, build_search(request)))
        else:
            context["pickform"] = pickform
            context["object_handle"] = handle
            context["object_type"] = item
            return render_to_response("pick.html", context)
    elif act == "add":
        event = Event(gramps_id=dji.get_next_id(Event, "E"))
        eventform = EventForm(instance=event)
        eventform.model = event
    elif act in ["view", "edit"]: 
        event = Event.objects.get(handle=handle)
        genlibevent = db.get_event_from_handle(handle)
        if genlibevent:
            date = genlibevent.get_date_object()
            event.text = dd(date)
        eventform = EventForm(instance=event)
        eventform.model = event
    elif act == "save": 
        event = Event.objects.get(handle=handle)
        eventform = EventForm(request.POST, instance=event)
        eventform.model = event
        if eventform.is_valid():
            update_last_changed(event, request.user.username)
            event = eventform.save()
            dji.rebuild_cache(event)
            act = "view"
        else:
            act = "edit"
    elif act == "create": 
        event = Event(handle=create_id())
        eventform = EventForm(request.POST, instance=event)
        eventform.model = event
        if eventform.is_valid():
            update_last_changed(event, request.user.username)
            event = eventform.save()
            dji.rebuild_cache(event)
            if add_to:
                item, handle = add_to
                model = dji.get_model(item)
                obj = model.objects.get(handle=handle)
                dji.add_event_ref_default(obj, event)
                dji.rebuild_cache(obj)                
                return redirect("/%s/%s#tab-events" % (item, handle))
            act = "view"
        else:
            act = "add"
    elif act == "delete": 
        event = Event.objects.get(handle=handle)
        event.delete()
        return redirect("/event/")
    else:
        raise Exception("Unhandled act: '%s'" % act)

    context["eventform"] = eventform
    context["object"] = event
    context["event"] = event
    context["action"] = act
    
    return render_to_response(view_template, context)
