$(document).ready(function() {
    let user_type_field = $("#id_type_selection");
    user_type_field.change(show_other_type);
    user_type_field.change();
    let has_plan_field = $("#id_has_plan");
    has_plan_field.change(show_plan_age);
    has_plan_field.change();

});

let transition_options = {
    duration: 400,
    easing: 'swing',
};


let show_other_type = function() {
    const USER_TYPE_OTHER = "5";
    const USER_TYPE_OWNER = "1";
    let user_type_val = $("#id_type_selection").val();
    let other_type_field = $('#id_type_other').parent();
    if (user_type_val == USER_TYPE_OTHER) {
        other_type_field.show(transition_options);
    } else {
        other_type_field.hide(transition_options);
    }
    if (user_type_val == USER_TYPE_OWNER) {
        $(".ownerQuestion:not(.dependent)").show(transition_options);
        show_plan_age();
    } else {
        $(".ownerQuestion").hide(transition_options);
    }

}

let show_plan_age = function() {
    const USER_TYPE_OWNER = "1";
    let has_plan_val = $("#id_has_plan").val();
    let user_type_val = $("#id_type_selection").val();
    let plan_age_field = $("#id_plan_date").parent();
    if (user_type_val == USER_TYPE_OWNER && has_plan_val == "True") {
        plan_age_field.show(transition_options);
    } else {
        plan_age_field.hide(transition_options);
    }
}