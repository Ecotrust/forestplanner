-------------------------------------------------------------
-- MDB Tools - A library for reading MS Access database files
-- Copyright (C) 2000-2004 Brian Bruns
-- Files in libmdb are licensed under LGPL and the utilities under
-- the GPL, see COPYING.LIB and COPYING files respectively.
-- Check out http://mdbtools.sourceforge.net
-------------------------------------------------------------

DROP TABLE TREE_LIVE;
CREATE TABLE TREE_LIVE
 (
	LIVE_ID			Int8, 
	PNTID			Int8, 
	CCID			Int8, 
	FCID			Int8, 
	PLTID			Int8, 
	LOC_ID			Int8, 
	PNT_NUM			Int4, 
	PLOT_TYPE			varchar (40), 
	DATA_SOURCE			varchar (30), 
	SOURCE_DB			varchar (30), 
	STATE			varchar (4), 
	PLOT			Int8, 
	ASSESSMENT_DATE			varchar (100), 
	SPP_SYMBOL			varchar (20), 
	SCIENTIFIC_NAME			varchar (200), 
	CON			varchar (2), 
	DBH_CM			double precision, 
	DBH_CLASS			double precision, 
	DBH_EST_METHOD			double precision, 
	BA_M2			double precision, 
	HT_M			double precision, 
	HT_EST_METHOD			Int4, 
	MOD_HTM_FVS			Int4, 
	FOR_SPEC			Int8, 
	AGE_BH			Int4, 
	CROWN_CLASS			Int4, 
	CROWN_RATIO			Int4, 
	HCB			double precision, 
	UCC			double precision, 
	VOL_M3			double precision, 
	CULL_CUBIC			double precision, 
	PLOT_SIZE			Int4, 
	TREE_COUNT			Int4, 
	SOURCE_ID			Int8, 
	BAPH_PNT			double precision, 
	BAPH_CC			double precision, 
	BAPH_FC			double precision, 
	BAPH_PLT			double precision, 
	TPH_PNT			double precision, 
	TPH_CC			double precision, 
	TPH_FC			double precision, 
	TPH_PLT			double precision, 
	PCTCOV_PNT			double precision, 
	PCTCOV_CC			double precision, 
	PCTCOV_FC			double precision, 
	PCTCOV_PLT			double precision, 
	REM_PNT			varchar (2), 
	REM_CC			varchar (2), 
	REM_FC			varchar (2), 
	REM_PLT			varchar (2), 
	VOLPH_PNT			double precision, 
	VOLPH_CC			double precision, 
	VOLPH_FC			double precision, 
	VOLPH_PLT			double precision, 
	IV_PNT			double precision, 
	IV_CC			double precision, 
	IV_FC			double precision, 
	IV_PLT			double precision, 
	BIOMPH_PNT			double precision, 
	BIOMPH_CC			double precision, 
	BIOMPH_FC			double precision, 
	BIOMPH_PLT			double precision
);
-- CREATE ANY INDEXES ...



-- CREATE ANY Relationships ...

-- relationships are not supported for postgres
