import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', '..'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
import ipdb
import json
import time
from trees.models import Stand, Scenario, Strata, ForestProperty, ScenarioNotRunnable, Rx, CarbonGroup
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist as DoesNotExist
# from django.test.client import Client
from django.contrib.gis.geos import GEOSGeometry
# from shapely.ops import cascaded_union
# from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt

# On exception, drop into ipdb in post-mortem mode
def info(type, value, tb):
    import traceback
    traceback.print_exception(type, value, tb)
    print
    ipdb.pm()
sys.excepthook = info

def cleanup():
    try:
        owner = User.objects.get(username='testOwner')
    except DoesNotExist:
        owner = False
    try:
        owner2 = User.objects.get(username='testOwner2')
    except DoesNotExist:
        owner2 = False
    try:
        manager = User.objects.get(username='testManager') 
    except DoesNotExist:
        manager = False
    try:
        testCarbonGroup = CarbonGroup.objects.get(name='test')
        CarbonGroup.delete(testCarbonGroup)
    except DoesNotExist:
        pass
    if owner:
        User.delete(owner)
    if owner2:
        User.delete(owner2)
    if manager:
        User.delete(manager)


if __name__ == "__main__":

    print ""

    #--------------------------------------------------------------------------#
    print "Prepare test environment"
    #--------------------------------------------------------------------------#  
    cleanup()

    #--------------------------------------------------------------------------#
    print "Create Users"
    #--------------------------------------------------------------------------#  
    owner = User.objects.create_user('testOwner', 'testOwner@ecotrust.org', password='test')
    owner2 = User.objects.create_user('testOwner2', 'testOwner2@ecotrust.org', password='test')
    manager = User.objects.create_user('testManager', 'testManager@ecotrust.org', password='test')  

    #--------------------------------------------------------------------------#
    print "Create Group"
    #--------------------------------------------------------------------------#
    testCarbonGroup, created = CarbonGroup.objects.get_or_create(user=manager, name='test', manager=manager, description='Demo test group', private=False)

    #--------------------------------------------------------------------------#
    # print "Assign Manager"  #Can this happen in "Create Group"?
    #--------------------------------------------------------------------------#

    #--------------------------------------------------------------------------#
    print "Associate User with Group"   
    #--------------------------------------------------------------------------#
    # testCarbonGroup.members.add(owner)
    testCarbonGroup.requestMembership(owner)
    assert(owner in testCarbonGroup.members.all())
    testCarbonGroup.requestMembership(owner2)
    memberships = testCarbonGroup.getMemberships(manager, 'pending')
    assert(memberships.count() == 2)
    ownerMemberships = [x for x in memberships if x.applicant == owner]
    assert(len(ownerMemberships) == 1)
    ownerMemberships[0].acceptMembership(manager)
    assert(ownerMemberships[0].status=='accepted')

    #--------------------------------------------------------------------------#
    print "Decline a membership request"   
    #--------------------------------------------------------------------------#

    owner2Memberships = [x for x in memberships if x.applicant == owner2]
    assert(len(owner2Memberships)==1)
    owner2Memberships[0].declineMembership(manager, 'You smell.')
    assert(owner2Memberships[0].status=='declined')
    assert(owner2Memberships[0].reason=='You smell.')

    #--------------------------------------------------------------------------#
    print "Load Property, Stands, Strata, ?_Scenario_?"
    #--------------------------------------------------------------------------#
    ### Load a json file?

    #--------------------------------------------------------------------------#
    print "Update Property With Group and Shared Scenario"
    #--------------------------------------------------------------------------#

    #--------------------------------------------------------------------------#
    print "Request group Users, Properties, Scenarios"
    #--------------------------------------------------------------------------#
    ### Check for users, properties, scenarios

    #--------------------------------------------------------------------------#
    print "Manager accepts/ignores the property"
    #--------------------------------------------------------------------------#
    ### Check for users, properties, scenarios

    #--------------------------------------------------------------------------#
    print "Manager changes membership status to denied"
    #--------------------------------------------------------------------------#
    ### Check for users, properties, scenarios

    #--------------------------------------------------------------------------#
    print "Clean up"
    #--------------------------------------------------------------------------#
    ### Remove everything added by the fixture.
    cleanup()

    # print
    # print "SUCCESS!"
    # print
    # print "... ignore the following GEOS error ... "
