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
from trees.models import Scenario, ForestProperty, CarbonGroup, Membership
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist as DoesNotExist

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
    owner2Scenarios = Scenario.objects.filter(user=owner2)
    for scenario in owner2Scenarios:
        for prop in scenario.forestproperty_set.all():
            prop.shared_scenario = None
            prop.save()
        Scenario.delete(scenario)

    ownerProperties = ForestProperty.objects.filter(user=owner)
    for fproperty in ownerProperties:
        ForestProperty.delete(fproperty)

    owner2Properties = ForestProperty.objects.filter(user=owner2)
    for fproperty in owner2Properties:
        ForestProperty.delete(fproperty)

    for cgroup in CarbonGroup.objects.filter(manager=manager):
        CarbonGroup.delete(cgroup)

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
    testCarbonGroup2, created = CarbonGroup.objects.get_or_create(user=manager, name='test2', manager=manager, description='Second demo test group', private=False)
    assert(len(CarbonGroup.objects.filter(manager=manager))==2)

    #--------------------------------------------------------------------------#
    # print "Assign Manager"  #Can this happen in "Create Group"?
    #--------------------------------------------------------------------------#

    #--------------------------------------------------------------------------#
    print "Associate User with Group"   
    #--------------------------------------------------------------------------#
    # testCarbonGroup.members.add(owner)
    testCarbonGroup.request_membership(owner)
    assert(owner in testCarbonGroup.members.all())
    testCarbonGroup.request_membership(owner2)
    memberships = testCarbonGroup.get_memberships('pending')
    assert(memberships.count() == 2)
    owner_memberships = [x for x in memberships if x.applicant == owner]
    assert(len(owner_memberships) == 1)
    owner_memberships[0].accept_membership(manager)
    assert(owner_memberships[0].status=='accepted')

    #--------------------------------------------------------------------------#
    print "Decline a membership request"   
    #--------------------------------------------------------------------------#

    owner2_memberships = [x for x in memberships if x.applicant == owner2]
    assert(len(owner2_memberships)==1)
    owner2_memberships[0].decline_membership(manager, 'You smell.')
    assert(owner2_memberships[0].status=='declined')
    assert(owner2_memberships[0].reason=='You smell.')

    #--------------------------------------------------------------------------#
    print "Load Property and Scenario"
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

    owner2Property = ForestProperty.objects.create(
        name='testProperty', 
        user=owner2, 
        geometry_final="MULTIPOLYGON (((-13649324.9062920007854700 5701104.7213275004178286, -13649329.6836060006171465 5700851.5236713001504540, -13649016.7695209998637438 5700846.7463570004329085, -13649324.9062920007854700 5701104.7213275004178286)))"
    )

    owner2Scenario = Scenario.objects.create(
        input_age_class=0, 
        input_target_carbon=True, 
        name='Grow Only',
        # output_scheduler_results="{u'3135': 2, u'3134': 2, u'3137': 0, u'3136': 0, u'3133': 4, u'3139': 3, u'3138': 4}",
        output_scheduler_results="{}",
        input_property=owner2Property,
        user=owner2,
        # input_rxs="{u'1559': 42, u'1558': 42, u'1560': 42, u'1561': 42, u'1562': 42, u'1563': 42, u'1564': 42}",
        input_rxs="{}",
        input_target_boardfeet=0,
        description="Test Scenario"
    )

    #--------------------------------------------------------------------------#
    print "Update Property With Group and Shared Scenario"
    #--------------------------------------------------------------------------#

    ownerProperty.share_with_group(testCarbonGroup, owner)
    ownerProperty.share_scenario(ownerScenario, owner)

    assert(len(testCarbonGroup.get_properties()) == 1)

    assert(len(owner.membership_set.all()) == 1)
    assert(len(owner.membership_set.filter(status='accepted')) == 1)
    assert(owner.membership_set.get(status='accepted').group == testCarbonGroup)
    assert(len(owner2.membership_set.all()) == 1)
    assert(len(owner2.membership_set.filter(status='accepted')) == 0)

    # Add a second user to the group to test ignoring properties.
    owner2_memberships[0].accept_membership(manager)

    assert(len(owner2.membership_set.filter(status='accepted')) == 1)

    owner2Property.share_with_group(testCarbonGroup, owner2)
    owner2Property.share_scenario(owner2Scenario, owner2)

    assert(len(testCarbonGroup.get_properties()) == 2)

    #--------------------------------------------------------------------------#
    print "Request group Users, Properties, Scenarios"
    #--------------------------------------------------------------------------#
    ### Check for users, properties, scenarios
    #check that we see both accepted memberships
    group_memberships = testCarbonGroup.get_memberships('accepted')
    assert(len(group_memberships)==2)
    #check that expected users are in the acceptedgroup memberships
    assert(group_memberships.get(applicant=owner))
    assert(group_memberships.get(applicant=owner2))
    assert(len(group_memberships.filter(applicant=manager))==0)
    groupUsers = [x.applicant for x in group_memberships]
    assert(owner in groupUsers)
    assert(owner2 in groupUsers)
    assert(manager not in groupUsers)
    #test that we can get properties
    groupProperties = testCarbonGroup.get_properties()
    assert(ownerProperty in groupProperties)
    assert(owner2Property in groupProperties)
    assert(testCarbonGroup.manager == manager)
    
    #--------------------------------------------------------------------------#
    print "Manager ignores a property"
    #--------------------------------------------------------------------------#
    testCarbonGroup.reject_property(owner2Property)
    assert(len(testCarbonGroup.get_properties())==1)
    assert(testCarbonGroup.get_properties()[0] == ownerProperty)

    #--------------------------------------------------------------------------#
    print "Manager changes membership status to denied"
    #--------------------------------------------------------------------------#
    owner2_memberships = testCarbonGroup.membership_set.filter(applicant=owner2)
    assert(len(owner2_memberships) == 1)
    owner2_memberships[0].decline_membership(manager, 'You still smell.')
    group_memberships = testCarbonGroup.get_memberships('accepted')
    assert(len(group_memberships) == 1)
    assert(group_memberships[0] == Membership.objects.get(applicant=owner, group=testCarbonGroup))
    declined_memberships = testCarbonGroup.get_memberships('declined')
    assert(len(declined_memberships) == 1)

    #--------------------------------------------------------------------------#
    print "Clean up"
    #--------------------------------------------------------------------------#
    ### Remove everything added by the fixture.
    cleanup()
