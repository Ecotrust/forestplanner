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
    ownerScenarios = Scenario.objects.filter(user=owner)
    for scenario in ownerScenarios:
        for prop in scenario.forestproperty_set.all():
            prop.shared_scenario = None
            prop.save()
        Scenario.delete(scenario)
    ownerProperties = ForestProperty.objects.filter(user=owner)
    for fproperty in ownerProperties:
        ForestProperty.delete(fproperty)
    try:
        testCarbonGroup = CarbonGroup.objects.get(name='test')
        CarbonGroup.delete(testCarbonGroup)
    except DoesNotExist:
        pass
    if owner:
        try: 
            ownerProperty = ForestProperty.objects.get(name='testProperty', user=owner)
            ForestProperty.delete(ownerProperty)
        except DoesNotExist:
            pass
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
    ownerProperty = ForestProperty.objects.create(
        name='testProperty', 
        user=owner, 
        geometry_final="MULTIPOLYGON (((-13649324.9062920007854700 5701104.7213275004178286, -13649329.6836060006171465 5700851.5236713001504540, -13649016.7695209998637438 5700846.7463570004329085, -13649324.9062920007854700 5701104.7213275004178286)))"
    )

    ownerScenario = Scenario.objects.create(
        input_age_class=0, 
        input_target_carbon=True, 
        name='Grow Only',
        # output_scheduler_results="{u'3135': 2, u'3134': 2, u'3137': 0, u'3136': 0, u'3133': 4, u'3139': 3, u'3138': 4}",
        output_scheduler_results="{}",
        input_property=ownerProperty,
        user=owner,
        # input_rxs="{u'1559': 42, u'1558': 42, u'1560': 42, u'1561': 42, u'1562': 42, u'1563': 42, u'1564': 42}",
        input_rxs="{}",
        input_target_boardfeet=0,
        description="Test Scenario"
    )
    ownerProperty.shareWithGroup(testCarbonGroup, owner)
    ownerProperty.shareScenario(ownerScenario, owner)

    assert(len(testCarbonGroup.getProposedProperties(manager)) == 1)



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
