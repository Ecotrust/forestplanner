# Create your views here.
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from madrona.features import get_feature_by_uid
from discovery.forms import DiscoveryStandForm
from django.contrib.auth.decorators import login_required

def index(request):
    return redirect('/discovery/landing/')

# landing page for non logged in users
def landing(request):
    if request.user.is_authenticated:
        return redirect('/discovery/stands/')
    else:
        context = {}
        return render(request, 'discovery/landing.html', context)

# account login page
def login(request):
    # TODO: write to handle wrong email address or password on login
    # if request.method == 'POST':
        # return django.contrib.auth.views.login()
    # else:
    context = {}
    return render(request, 'discovery/account/login.html', context)

# account register / signup page
def signup(request):
    context = {
        'title': 'Forest Discovery',
    }
    return render(request, 'discovery/account/signup.html', context)

# account password reset and username recovery page
def password_reset(request):
    context = {}
    return render(request, 'discovery/account/password_reset.html', context)

# account profile page
def user_profile(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % ('/discovery/auth/login/', request.path))
    else:
        context = {}
        return render(request, 'discovery/account/profile.html', context)

@login_required
def example_stands(request):
    from discovery.models import ExampleStand

    stands = []
    for stand in ExampleStand.objects.all():
        stands.append(stand.to_grid())

    context = {
        'user': request.user,
        'title': 'Existing Stands',
        'grid_data': stands,
        'grid_defaults': {
            'image': settings.DEFAULT_STAND_IMAGE,
            'splash_image': settings.DEFAULT_STAND_SPLASH,
        },
        # use button_text and button_action together
        'button_text': None,
        'button_action': None,
        'help_title': "Help",
        'help_flatblock': 'help-example-stands'
    }

    return render(request, 'discovery/stand_grid.html', context)

@login_required
def create_stand_from_example(request, example_stand_uid):
    from discovery.models import DiscoveryStand
    from trees.models import Strata
    feature = get_feature_by_uid(example_stand_uid)
    discovery_stand = DiscoveryStand.objects.create(user=request.user, name=feature.name)
    discovery_stand.save(geometry_final=feature.geometry_final)

    stand_classes = []
    search_tpa = 0
    for treelist in feature.standlistentry_set.all():
        size_class = eval(str(treelist.size_class))
        if type(size_class) == tuple and len(size_class) > 0:
            if len(size_class) > 1:
                min_size = size_class[0]
                max_size = size_class[1]
            else:
                min_size = size_class[0]
                max_size = size_class[0]
        elif type(size_class) == int or type(size_class) == float:
            min_size = int(size_class)
            max_size = int(size_class)
        else:
            min_size = 0
            max_size = 0

        stand_classes.append([treelist.species, int(min_size), int(max_size), treelist.tpa])
        search_tpa += treelist.tpa
    standlist = {
        'classes': stand_classes,
        'property': discovery_stand.lot_property.uid
    }

    #   Create trees.models.strata
    strata = Strata.objects.create(user=request.user, name=feature.name, search_age=feature.age, search_tpa=search_tpa, stand_list=standlist)
    strata.save()

    stand = discovery_stand.get_stand()
    stand.strata = strata
    stand.save()

    strata.add_to_collection(discovery_stand.lot_property)

    return forest_profile(request, discovery_stand.uid)

# Display user's existing stands
@login_required
def stands(request):
    from discovery.models import DiscoveryStand
    from datetime import date

    stands = []
    for stand in DiscoveryStand.objects.filter(user=request.user):
        stands.append(stand.to_grid())

    context = {
        'user': request.user,
        'title': 'stands',
        'grid_data': stands,
        'grid_defaults': {
            'image': settings.DEFAULT_STAND_IMAGE,
            'splash_image': settings.DEFAULT_STAND_SPLASH,
        },
        # use button_text and button_action together
        'button_text': '+ Add a new property',
        'button_action': '/discovery/find_your_forest/',
    }
    return render(request, 'discovery/stand_grid.html', context)

def get_modal_content(request, card_type, uid):
    feature = get_feature_by_uid(uid)
    if card_type == 'stand':
        if feature.splash_image.name:
            splash_image = feature.splash_image.url
        else:
            splash_image = settings.DEFAULT_STAND_SPLASH
        context = {
            'TITLE': feature.name,
            'SPLASH_IMAGE': splash_image,
            'LINKS': [
                {'href': '/discovery/map/%s/' % uid, 'label': 'Edit Stand',},
            ]
        }
        stand = feature.get_stand()
        if stand:
            if not stand.strata:
                context['LINKS'].append({'href': '/discovery/collect_data/%s/' % uid, 'label': 'Collect Data',})
            else:
                context['LINKS'].append({'href': '/discovery/enter_stand_table/%s/' % uid, 'label': 'Edit Tree List',})
                context['LINKS'].append({'href': '/discovery/forest_profile/%s/' % uid, 'label': 'View Profile',})
                context['LINKS'].append({'href': '/discovery/compage_outcomes/%s/' % uid, 'label': 'Compare Outcomes',})
                if feature.lot_property.scenario_set.all().count() > 0:
                    context['LINKS'].append({'href': '/discovery/compare_outcomes/%s/' % uid, 'label': 'View Report',})
        context['LINKS'].append({'href': '/features/generic-links/links/delete/%s/' % uid, 'label': 'Delete Stand', 'class':'delete',})

    elif card_type == 'example_stand':
        if feature.splash_image.name:
            splash_image = feature.splash_image.url
        else:
            splash_image = settings.DEFAULT_STAND_SPLASH
        context = {
            'TITLE': feature.name,
            'SPLASH_IMAGE': splash_image,
            'CONTENT': feature.content,
            'LINKS': [
                {'href': '/discovery/example_stands/create_stand/%s/' % uid, 'label': 'Select this Stand',},
            ],
        }
    else:
        context = {}
    try:
        return render(
            request,
            'discovery/%s/modal.html' % card_type,
            context
        )
    except Exception as e:
        return render(
            request,
            'discovery/stand/modal.html',
            context
        )

# find your forest page
@login_required
def find_your_forest(request):
    context = {
        'title': 'Find Your Forest',
        'flatblock_slug': 'find-your-forest',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Choose an existing property',
        'act_btn_one_action': '/discovery/example_stands/',
        'act_btn_two_text': 'Map your own property',
        'act_btn_two_action': '/discovery/map/',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

# collect data page
@login_required
def collect_data(request, discovery_stand_uid):
    if settings.IMPORT_TREELIST:
        next_action = '/discovery/enter_data/%s/' % discovery_stand_uid
    else:
        next_action = '/discovery/enter_stand_table/%s/' % discovery_stand_uid
    context = {
        'title': 'Collect data',
        # 'flatblock_slug': 'collect-data',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Download tree list spreadsheet template',
        'act_btn_one_action': '',
        'act_btn_two_text': 'Download a stand table PDF template',
        'act_btn_two_action': '',
        # cta below action buttons options
        ## should this button be displayed
        'use_step_btn': True,
        'step_btn_action': next_action,
        'step_btn_text': 'Enter data now',
    }
    return render(request, 'discovery/collect_data.html', context)

# enter data page
@login_required
def enter_data(request):
    context = {
        'title': 'Enter data',
        'flatblock_slug': 'enter-data',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        # specific for action buttons template
        'act_btn_one_text': 'Upload a new tree list',
        'act_btn_one_action': '',
        'act_btn_two_text': 'Enter a new stand table',
        'act_btn_two_action': '/discovery/enter_stand_table/',
        # cta below action buttons options
        ## should this button be displayed
        ### Todo: may change to insert a disabled parameter
        ### see comment #1 : https://xd.adobe.com/view/f5cb1927-f0b7-4642-5232-f30339f78d62-83fa/screen/e8c2b162-e3c5-450f-a39e-bb71e177f1fa/Enter-data
        'use_step_btn': True,
        'step_btn_action': '/discovery/forest_profile/',
        'step_btn_text': 'View forest profile',
    }
    return render(request, 'discovery/common/action_buttons.html', context)

def stand_list_form_to_json(form, prop_uid):
    ret_val = {}
    classes = []
    for index in range(0, int(form.data['form-TOTAL_FORMS'])):
        if not form.data['form-%d-species' % index] == '' and not ('form-%d-DELETE' % index in form.data.keys() and form.data['form-%d-DELETE' % index] == 'on'):
            new_class = [
                form.data['form-%d-species' % index],
                int(eval(form.data['form-%d-size_class' % index])[0]),
                int(eval(form.data['form-%d-size_class' % index])[1]),
                int(form.data['form-%d-tpa' % index])
            ]
            classes.append(new_class)
    ret_val['classes'] = classes
    ret_val['property'] = prop_uid
    return ret_val

def get_tpa_from_stand_list(standlist):
    tpa = 0
    for class_item in standlist['classes']:
        tpa += class_item[3]
    return tpa

# enter new stand table page
@login_required
def enter_stand_table(request, discovery_stand_uid):
    from django.forms import formset_factory, ChoiceField
    from discovery.forms import DiscoveryStandListEntryForm
    from trees.models import Strata
    from trees.views import get_species_sizecls_json
    from django.forms import widgets as form_widgets

    error_msgs = []
    stand = get_feature_by_uid(discovery_stand_uid)
    choice_json = get_species_sizecls_json(stand.variant)
    prop_stand = stand.get_stand()
    if not prop_stand:
        return map(request, discovery_stand_uid)
    DiscoveryStandListEntryFormSet = formset_factory(
        DiscoveryStandListEntryForm,
        can_delete=True,
        extra=100,
    )
    if request.method == 'POST':
        POST = request.POST.copy()
        stand_age = POST.pop('stand_age')
        if type(stand_age) == list and len(stand_age) == 1:
            stand_age = int(stand_age[0])
        formset = DiscoveryStandListEntryFormSet(POST, request.FILES)
        if formset.is_valid():
            standlist = stand_list_form_to_json(formset, stand.lot_property.uid)
            if not standlist['classes'] == []:
                search_tpa = get_tpa_from_stand_list(standlist)
                if prop_stand.strata:
                    prop_stand.strata.name = stand.name
                    prop_stand.strata.stand_list = standlist
                    prop_stand.strata.search_age = stand_age
                    prop_stand.strata.search_tpa = search_tpa
                    prop_stand.strata.save()
                else:
                    # create strata
                    prop_strata = Strata.objects.create(user=request.user, name=stand.name, search_age=stand_age, search_tpa=search_tpa, stand_list=standlist)
                    prop_stand.strata = prop_strata
                    prop_stand.save()
                    prop_strata.add_to_collection(stand.lot_property)
                return HttpResponse(status=204)
            else:
                error_msgs.append("You must provide at least 1 stand table record.")
        if len(error_msgs) == 0:
            error_msgs.append("Unknown error occurred. Please double check your form.")

    # If method is GET or POST failed
    initial = False
    stand_age = None
    if prop_stand and prop_stand.strata:
        initial = []
        stand_age = int(prop_stand.strata.search_age)
        for list_item in prop_stand.strata.stand_list['classes']:
            initial.append({
                'species': list_item[0],
                'size_class': str((list_item[1], list_item[2])),
                'tpa': list_item[3]
            })
    if initial:
        formset = DiscoveryStandListEntryFormSet(initial=initial)
    else:
        formset = DiscoveryStandListEntryFormSet()

    species_choice_list = [('', '----')] + [(x['species'], x['species']) for x in choice_json]
    for form in formset.forms:
        form.fields['species'] = ChoiceField(choices=species_choice_list)
        if 'species' in form.initial.keys():
            size_classes = [x for x in choice_json if x['species'] == form.initial['species']][0]['size_classes']
            size_choices = [(str((int(x['min']), int(x['max']))), '%d" to %d"' % (x['min'], x['max'])) for x in size_classes]
        else:
            size_choices = (('', '(Select a species first)'),)
        form.fields['size_class'] = ChoiceField(choices=size_choices)
    context = {
        'title': 'Enter stand table',
        'subtitle': stand.name,
        'flatblock_slug': 'enter-stand-table',
        # use button_text and button_action together
        'button_text': 'Help',
        'button_action': '',
        # specific for data entry template

        # cta below action buttons options
        ## should this button be displayed
        'use_step_btn': True,
        # 'step_btn_action': '#',
        'step_btn_text': 'View forest profile',
        'stand_age': stand_age,
        'formset': formset,
        'choice_json': choice_json,
        'UID': discovery_stand_uid,
        'error_msgs': error_msgs,
    }
    return render(request, 'discovery/common/data_table.html', context)

# view for web map of property
@login_required
def map(request, discovery_stand_uid=None):
    if discovery_stand_uid:
        discovery_stand = get_feature_by_uid(discovery_stand_uid)
        form = DiscoveryStandForm({
            'name': discovery_stand.name,
            'geometry_final': discovery_stand.get_stand().geometry_final.wkt,
            'user': request.user.pk,
            'pk':discovery_stand.pk,
        })
    else:
        form = DiscoveryStandForm()
    form_user = request.user
    form.fields['user'].initial = form_user
    context = {
        'title': 'Map your forest stand',
        'flatblock_slug': 'map-your-property',
        # use button_text and button_action together
        # 'button_text': 'Help',
        'button_action': '',
        'DISCOVERYSTAND_FORM': form,
    }
    return render(request, 'discovery/map.html', context)

# forest profile page
@login_required
def forest_profile(request, discovery_stand_uid):
    stand = get_feature_by_uid(discovery_stand_uid)
    profile_columns = []
    # Forest Type
    forest_type_col = {
        'title': 'Forest Type',
        'entries': []
    }
    # get total basal area
    stand_stats = stand.get_stand_stats()
    # get predominant species by basal area
    #  Or "mix" with species w/ gte 25% BA
    #  Or "[hard/soft]wood mix"
    forest_type = stand_stats['forest_type']
    forest_type_col['entries'].append({
        'label': False,
        'value': forest_type
    })
    forest_type_col['entries'].append({
        'label': False,
        'value': '<div><svg width="300" height="300" id="species-pie-chart"></svg></div>'
    })
    profile_columns.append(forest_type_col)

    # Tree Size
    # Get QMD
    # Get "Size Class"
    tree_size_col = {
        'title': 'Tree Size',
        'entries': [
            {
                'label': False,
                'value': stand_stats['tree_size']['size_class']
            },
            {
                'label': 'Quadratic Mean Diameter (QMD) =',
                'value': '%.1f"' % round(stand_stats['tree_size']['qmd'],1)
            },
        ]
    }
    profile_columns.append(tree_size_col)

    # TODO:
    # Stocking
    # Get Basal Area (from above)
    # Get TPA (from strata)
    stocking_col = {
        'title': 'Stocking',
        'entries': [
            {
                'label': None,
                'value': "%.1f ft<sup>2</sup>/ac basal area (BA)" % round(stand_stats['basal_area_dict']['total'],1)
            },
            {
                'label': None,
                'value': "%s trees per acre (TPA)" % stand_stats['tpa']
            }
        ]
    }
    profile_columns.append(stocking_col)

    # Structure
    #   Need more input from DD
    structure_col = {
        'title': 'Structure',
        'entries': []
    }
    profile_columns.append(structure_col)

    context = {
        'title': 'Forest profile',
        'subtitle': stand.name,
        'flatblock_slug': 'forest-profile',
        # use button_text and button_action together
        'button_text': 'WATCH TUTORIAL',
        'button_action': '',
        'profile_columns': profile_columns,
        'stand_stats': stand_stats,
    }
    return render(request, 'discovery/forest_profile.html', context)

# overwrite static content in lot app about.html
def about(request):
    context = {}
    return render(request, 'discovery/common/about.html', context)

# overwrite satic content in lot app documenation
def documentation(request):
    context = {}
    return render(request, 'discovery/common/documentation.html', context)
