# Forest Planner
## Using Custom Forest Inventory Data in Forest Planner

Author: Matthew Perry <perrygeo@gmail.com>

Date: Mar 23, 2015

## Introduction

The Ecotrust Forest Planner allows users to map their forest properties and evaluate future scenarios based on a database of growth and yield data derived from public forest inventory plots. The user's forest type is matched against the most similar public plot in process known as "Nearest Neighbor"

This document outlines the technical design details for new functionality allowing Forest Planner to accept other sources of custom inventory data. This will provide more precise and accurate reports driven by the growth and yield modeling on user's own data instead of the "nearest" public inventory data.

This increased accuracy comes at a price; forest planner site administrators must take on additional responsibility on behalf of the user to:

* clean and process potentially messy inventory and spatial data
* model the growth and yield using the existing FVS prescriptions (rx)
* associate stand spatial data with inventory
* append the growth and yield data to the forest planner database
* optionally upload spatial data on behalf of the user to create a new property


The intended audience for this document are site administrators or software developers
involved in building or maintaining the forest planner code. It is not intended
as a document for end users (unless they care deeply about the details).


![Forest Planner Inventory Workflow, public and custom](forestplanner.png)


## Definition of terms


## Software Design

### Shapefile import

The shapefile import functionality allows users or site administrators to create
a new property and populate it with stands corresponding to the polygons in the shapefile. This can be accessed by the user through the web interface (The "Upload" functionality). We will focus on the programmatic interface as per the intended audience.

 The programmatic interface includes two components:

* `lot.trees.views.upload_stands` is a django view which accepts an HTTP request, handles the uploaded file and, assuming the data are valid, creates a `ForestProperty` and `Stands` for the user based on the uploaded file. There is also an option to populate an existing `ForestProperty` though it is not exposed through the web interface.

* `lot.trees.utils.StandImporter` is the Python class which performs the heavy lifting of
validating the data and writing it to the database.

#### Data requirements

To incorporate custom user inventory, we need a mechanism to associate stands with specific forest plots. Uploading spatial data is currently the one and only mechanism for a user to associate stands with inventory records via the web interface.

It is required that uploaded spatial data:

1. have a `condid` attribute field containing integer values corresponding to the `condid` of the associated inventory records.
2. have all `condid`s specified in the data already exist in the `fvsaggregate` table for the variant in which the property falls.
3. have satisfied all previous constraints on shapefile uploads.

#### upload_stands

If any of the above requirements are not met, the `upload_stands` view will reject the data and return a HTTP response with a `400` status code.

#### StandImporter

The `StandImporter` class must perform additional tasks in order to associate the spatial data with custom user inventory. Specifically,

1. Validate the presence and proper data type of the `condid` column. The presence of a `condid` column forces this behavior - if you don't want to use inventory, remove the `condid` field from the shapefile.
2. Validate that all `condids` specified have corresponding records in the `trees_fvsaggregate` table
3. If all stands are valid, insert into the appropriate tables and populate the `condid` *and* `locked_condid` column of the Stand.
    * If any stand has a non-null `locked_condid`, it is assumed to be locked and will no longer be mutated by the NearestNeighbor service.
    * If a property contains any stands that are locked, the entire property is assumed to be locked which has implications
    for user interface and other parts of the system.
4. ** TODO  Populating forest types from condids ?  **

### FVSAggregate model

On importing user's stands, we need to confirm that there exist valid records for the associated condition in the fvsaggregate table. To accomplish this, we add a `valid_condids` classmethod to `FVSAggregate`. As a classmethod, it can be called on the class rather than an instance, allowing for simply:

    pn = FVSVariant.objects.get(code="PN")  # get pacific northwest variant
    FVSAggregate.valid_condids(pn)

This returns a list of all "valid" condids for this variant. At this point, validity is defined loosely - it currently just creates a list of condids with that variant. More advanced logic (e.g. checking that they have all necessary rxs, etc) can be added as required. Until then, it's up to the site administrators to ensure that any data added to the fvsaggregate table is done cleanly.

Because the query may be very computationally expensive, this method is cached. Therefore it is required to clear the cache when new data is added. This can be done using Redis directly:

    $ redis-cli
    redis 127.0.0.1:6379> select 1
    OK
    redis 127.0.0.1:6379[1]> keys *valid_condids*
    1) ":1:fvsaggregate_valid_condids_varWC"
    redis 127.0.0.1:6379[1]> DEL ":1:fvsaggregate_valid_condids_varWC"
    (integer) 1
    redis 127.0.0.1:6379[1]> keys *valid_condids*
    (empty list or set)

### Nearest Neighbor

The nearest neighbor module populates the `condid` of each stand asynchronously based on public forest inventory data, assuming that forest types and terrain information are available for a given stand. In the case of custom user inventory, we want to bypass the nearest neighbor by assigning a `condid` directly at import.

We must ensure that locked stands are never disassociated with their inventory; if for whatever reason the nearest neighbor is run on a locked stand, it will simply set the stand's `condid` equal to `locked_condid`. This effectively makes it impossible to wipe out the inventory link by accidentally running the nearest neighbor.

Notably, this allows database administrators to run the nearest neighbor on *all* stands (e.g. during a large data migration involving new public inventory) without worrying how it might affect locked stands.

### Model and database schema changes
The `Stand` model will will require a new `locked_cond_id` integer field
which serves as a key to the `trees_fvsaggregate.cond`. The new field will be nullable, null by default and will require a schema migration.

 Just as with the `trees_stand.cond_id` field, the new `trees_stand.locked_cond_id` column is not enforced as a foreign key due to practical constraints when importing data - the site admin is responsible for maintaining the foreign key referential integrity through proper data practices. In other words, if a stand has a `locked_cond_id` or `cond_id` which points to a non-existent record in `fvsaggregate`, you're going to have problems. The import procedure will enforce this *at import* but further data migrations will need to keep this in mind.

Additionally, the `Stand` model will have an additional `is_locked` property that will return a boolean indicating the presence of a `locked_cond_id`; it is effectively a semantic convinience for checking if `locked_cond_id` is null.

Similarly, the `ForestProperty` model will also have an additional `is_locked` property if *any* stands belonging to it are locked.

### User interface

In the stand editing and creation UI (Step 2), we disallow creation of new stands for locked properties. This is accomplished by hiding the create buttons if property is locked and will not necessarily be enforced at the HTTP or Python API level.

In the forest type UI (Step 3), we continue to show forest types - in the case of locked properties this **TODO may be condids?** -  but will issue a highly visible warning that any changes will not override the custom inventory (ie. it is useless to edit forest types)


### import_gyb management command

Since the growth-yield-batch system will be used to perform growth and yield modeling, forest planner contains a python function and a wrapper django management command, `import_gyb`, to facilitate loading data.

The command takes a single required argument:

* `gyb_db`: Path to the sqlite database created by `growth-yield-batch`

All imports take place in the context of a database transaction such that any error will rightfully cause the entire import to roll back to it's previous state and error out - it is an all-or-none process.

Note that importing data in this manner (or by manually appending it to the fvsaggregate table) will *not* necessarily make that inventory plot available to other user via the nearest neighbor system. Other data is required to accomplish this and it is outside of the scope of this document.

An example usage of the command would be:

```
python manage.py import_gyb gyb_data/final/data.db
```

## Loading data from custom user inventory

When Forest Planner site administrators receive inventory data/spatial data from a qualified user, that data must be processed and imported into the system. Depending on the quality of the source data, this can involve different steps and effort may be highly variable depending on data quality.

The general process, as it applies to any user inventory regardless of data quality, proceeds as follows:

1. Ensure that each plot in the user inventory is assigned a globally unique `condid`. They must not conflict with public inventory `condid`s or with any other user's `condid`s including their own. Unique `condid`s are crucial to the system and determining them for each plot within a user's inventory should *always* be the first step. Remember that `condid` is an integer and, if it is desired to have *identifiable* ids, it is the responsibility of the forest planner database manager to develop and implement a system for managing ids in such a manner.
2. Process inventory data for use with the growth-yield-batch system and run the model. The rxs for each variant must be identical or practically identical - small changes to FVS keyfiles are OK as long as the intent of the prescription is unaltered.
3. Quality assurance and data quality control
4. Create and populate the `condid` column for the user's spatial data, creating the linkage between their stands and their inventory data.
5. Import the growth and yield results into the forest planner database using the `import_gyb` command.
6. Upload spatial data to an internal account and perform manual QA/QC using the web interface to ensure that stands and inventory have been successfully linked and that scenario calculations are accurate.

### Data Analysis Caveats

This section highlights some of the quirks in the forest planner data model that should be kept in mind while preparing user inventory data.

In the forest planner, temporal **offsets** are encoded as integers from 0 to 4 where an offset of 1 indicates a 5-year delay in harvest. However, the growth-yield-batch system encodes offsets as integers representing the actual number of years. While the later is more flexible and more widely applicable outside the context of the forest planner, the former is more strict and ensures that growth and yield data conform to a standard pattern of offsets.

The implications of this design decision are handled by the `import_gyb` management command but if you choose another route for loading fvs data, you must handle this by dividing the gyb offset by 5 and ensuring forestplanner offset is an integer between 0 to 4, inclusive. Failure to do so will lead to all sorts of indeterminate bugs and inaccuracies.

Related to offsets, the GYB system will not (by default) apply offsets to Grow-Only prescriptions, assumed to be `rx == 1`. The forest planner, when applying offsets to scenariostands in `trees.tasks.schedule_harvest`, will set offset to zero for any grow-only stands. So, under normal usage, this should not be an issue. If, for whatever reason, the scenariostands with rx 1 get assigned a non-zero offset and the gyb data is missing non-zero offsets for rx 1, the SQL joins will drop those stands entirely.

### Example Workflow
workflow docs for David and Ryan re: importing from gyb,

### Discussion of ongoing maintenance and potential issues

mixing locked and unlocked stands (property would appear locked)


