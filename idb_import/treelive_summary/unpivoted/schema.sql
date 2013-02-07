DROP TABLE TREELIVE_SUMMARY;
CREATE TABLE TREELIVE_SUMMARY
(
    CLASS_ID        Int8,
	PLOT_ID			Int8, 
	COND_ID			Int8, 
	VARNAME			varchar (60), 
	FIA_FOREST_TYPE_NAME			varchar (60), 
	CALC_DBH_CLASS			Float8, 
	CALC_TREE_COUNT			Int4, 
	SumOfTPA			Float8, 
	AvgOfTPA			Float8, 
	SumOfBA_FT2_AC			Float8, 
	AvgOfBA_FT2_AC			Float8, 
	AvgOfHT_FT			Float8, 
	AvgOfDBH_IN			Float8, 
	AvgOfAge_BH			Float8, 
	TOTAL_BA_FT2_AC			Float8, 
	COUNT_SPECIESSIZECLASSES			Int4, 
	PCT_OF_TOTALBA			Float8
);
-- CREATE ANY INDEXES ...
create index treelive_summary_foresttype_idx on treelive_summary using hash(FIA_FOREST_TYPE_NAME);
create index treelive_summary_class_idx on treelive_summary using btree(CALC_DBH_CLASS);

