#ifndef Schedule_H
#define Schedule_H


//#include "other_file.h"

// ========================================================================== //
// ========================================================================== //

enum {NPOLY = 29750}; //#total number of stands
enum {NSTRATA = 165};//the max value of the input plots
enum {NSTRATA_MAP = 55}; //#number of plots?
enum {NPX = 6}; //#number of prescriptions
enum {NOFF = 9}; //#number of offsets
enum {NTP = 39}; //#number of time periods
enum {NSPECIES = 21}; // number of species groups

const double TO_MMBFPY_DENOM = 5000000.0; // 1 million * FVS sim period (for cut volumes)
const double TO_MMCUBFPY_DENOM = 5000000.0;
const double TO_MMBFPY_DENOM_LIVE = 1000000.0; // live volume accounting does not get divided by sim period
const double MIN_ACREAGE_FOR_ADJ_CHECK = 20.0; // below this acreage, a polygon will skip adjacency checks
const double CLEARCUT_TEST_THRESHHOLD = 80; // adj polys will not be simul cut if both exceed this cut val in BF

const int YOUNG_AGE = 1;
const int INTERMEDIATE_AGE = 2;
const int ADVANCED_AGE = 3;

const float MIN_ADVANCED_PCT = 0.0;
const float CARBON_WEIGHT = 0;  // how much importance you want to give carbon in the objective function
                //Set CARBON_WEIGHT to 0 to ignore it.

// SIMULATED ANNEALING CONTROL VARS -- shouldn't really need to change, but just in case

const int SA_START_TEMPERATURE = 10; // anneal start temp -- higher = more random deviations
const int SA_POLY_TESTS_PER_TEMP = 1000; // number of polygons checked per temperature iteration
const double SA_TEMP_DECAY_PER_ITER = 0.997; // multiplier used to decay temperature at end of each iter
const double SA_MINIMUM_TEMP = 0.05; // temperature at which annealing process ends


enum {MAX_STR_LENGTH = 256};

#endif /* Schedule_H */



