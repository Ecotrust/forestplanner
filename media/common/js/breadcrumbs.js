if (typeof app === 'undefined') {
    app = {};
}

app.breadCrumbs = {
    breadcrumbs: ko.observableArray(),

    // ko method to determine if we are the last
    isLast: function (crumb) {
        return this.breadcrumbs.indexOf(crumb) === this.breadcrumbs().length - 1;
    },

    // method to update breadcrumbs
    update: function (crumb) {
        var index, lastCrumb = this.breadcrumbs.pop();

        if (crumb.url !== lastCrumb.url) {
            this.breadcrumbs.push(lastCrumb);
        }
        this.breadcrumbs.push(crumb);
        $.each(this.breadcrumbs(), function (i, item) {
            if (item.url === crumb.url && item.name === crumb.name) {
                index = i;
                return false;
            }
        });
        this.breadcrumbs.splice(index + 1, this.breadcrumbs().length);
    }
};
var crumbsEl = document.getElementById('breadcrumbs');
if (crumbsEl) {
	ko.applyBindings(app.breadCrumbs, crumbsEl);
}
