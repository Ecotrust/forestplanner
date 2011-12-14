/******************************************************************************\
 *
 * Schedule.c
 * 
 * This code implements a simulated annealing algorithm to schedule harvest
 * of forest land based on the growth and yield output.
 *
 * This code was adapted from work led by John Sessions at OSU and has been
 * adapted to fit within the Ecotrust build environment.  The biggest changes
 * include the ability to build in the Linux environment for easy integration
 * with other Open Source tools available on that platform.
 *
\******************************************************************************/

#include "schedule.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

const int OBJ_EXPONENT = 2;

/******************************************************************************\
 *
 * Global Variables
 *
\******************************************************************************/
// Original arrays
char own_type[NPOLY+1][MAX_STR_LENGTH];
char species_map[NSPECIES][MAX_STR_LENGTH];
int species_count = 0;
double x_cutbfvol[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1];    
double x_cutbfvol_spec[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1][NSPECIES];    
double x_cutcubvol[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1];    
double x_cutcubvol_spec[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1][NSPECIES];
double x_C_tons[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1]; 
int x_age[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1]; 
double x_livevol[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1];    
int x_cutbfvol_valid[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1];    
int x_cutcubvol_valid[NSTRATA_MAP+1][NPX+1][NOFF+1][NTP+1];    
double acres[NPOLY+1];
// Arrays added by APR

int strata_count = 0;

int poly_biz_px[NPOLY+1];
int beg_adj_ptr[NPOLY+1];
int end_adj_ptr[NPOLY+1];
int adj_list[(NPOLY*5)+1]; // This needs to be allocated by size of adjacency list
int cubic_data = 1;     //boolean - switches to track cubic data if it exists

FILE* log_fout;
char gs[MAX_STR_LENGTH];

char (*strata_map)[MAX_STR_LENGTH];
char (*strata_link)[MAX_STR_LENGTH];


/******************************************************************************\
 * Function:: logit
 *
 * @log_level - level for logging the debug output
 * @string_to_log - Output to log
 * 
 * @void - No return value
 *
\******************************************************************************/
void logit(int log_level, char* string_to_log)
{
  printf("%s\n",string_to_log);
  if ( log_level > 1 )
    {
      fprintf(log_fout, "%s\n", string_to_log);
    } 
}


/******************************************************************************\
 * Function:: read_in_adj_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_adj_file(char* fname)
{
  FILE *fin;
  int fscanf_line = EOF;
  int old_poly = 0;
  int new_poly = 0;
  int number_of_adj_records = 0;
  int i;
  char col_header[MAX_STR_LENGTH];
  char* curr_field;

  // Check that the file we are reading in is OK
  if ((fin = fopen(fname, "r")) == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    exit(1);
  }

  i=1;
  // Now to read it in...
  //while ((fscanf_line = fscanf(fin,"%d,%d",&new_poly, &adj_list[i])) != EOF)
  while (fgets( col_header, MAX_STR_LENGTH, fin))
  {
        curr_field = strtok( col_header, ",");
        for ( i = 0; i < 2; i++ )
        {    
            switch(i)
            {
                case 0: new_poly = atoi( curr_field ); break;
                case 1: adj_list[i] = atoi( curr_field ); break;
            }
            curr_field = strtok( NULL, ",");
        }
  
      // check if we got a header row
      if ( new_poly == 0 && adj_list[i] == 0)
	{
	  // chomp it up
	  printf( "adj file header found\n" ); 
	  continue;
	}

      if (new_poly != old_poly)
	{
	  if (old_poly != 0)
	    {
	      // We need to mark the end pointer for the previous (if there is one)
	      //int end_adj_ptr[NPOLY+1];
	      end_adj_ptr[old_poly] = i-1;
	    }
	  // We need to mark the start of the next one (if there is one)
	  //int beg_adj_ptr[NPOLY+1];
	  beg_adj_ptr[new_poly] = i;
	}
      old_poly = new_poly;
      i++;
    }
  // Need to close off the last poly
  end_adj_ptr[old_poly] = i-1;
  number_of_adj_records = i-1;

  // DEBUG CODE ////////////////////////////////////////////////
  // Print out the first twenty
  //for (i=1;i<=20;i++)
  //  {
  //    printf("Record %d = %d\n",i,adj_list[i]);
  //  }
  //printf("\n\n\n");
  //// And last twenty
  //for (i=number_of_adj_records-20;i<=number_of_adj_records;i++)
  //  {
  //    printf("Record %d = %d\n",i,adj_list[i]);
  //  }
  //printf("\n\n\n");
  //for (i=1;i<=10;i++)
  //  {
  //    printf("Beg Adj for poly %d = %d\n",i,beg_adj_ptr[i]);
  //    printf("End Adj for poly %d = %d\n",i,end_adj_ptr[i]);
  //  }
  // DEBUG CODE ////////////////////////////////////////////////

  // Close the file handle
  fclose(fin);
  // Return sucess
  return 1;
}


/******************************************************************************\
 * Function:: load_new_strata
 *
 * @strata - Value of true strata that will be indexed and a key generated
 * 
 * @int - New strata key value
 *
\******************************************************************************/
int load_new_strata(char* strata)
{
  int key = -1;
  int i;
  

  // Look for the strata to see if it is already loaded
  for(i=0;i<strata_count;i++)
  {
    if (strata_map[i] != NULL && strcmp(strata,strata_map[i])==0)
    {
      // We have found a pre-existing strata
      key = i;
    }
  }
  // If it is not already loaded, make a new entry in the hash
  if (key == -1)
    {
      // We did not find a pre-existing one, so push it onto the array
      strcpy(strata_map[strata_count],strata);
      key = strata_count;


      strata_count++;
      
      // check to see if this strata is mapped to any polygons in the strata_link array
      int j;
      int found = -1;
      for (j = 0; j < NPOLY+1; j++)
      {
        if ( strcmp(strata_link[j],strata) == 0 || atoi(strata_link[j]) == atoi(strata) )
        {
            found = j;
            break;
        }
      }
      
      if ( found == -1 )
      {
        sprintf(gs, "WARNING: strata %s appears in FVS data but is not mapped to any polygon", strata ); 
        logit(2,gs);        
      }
    }
  
  // Return the key value
  return key;
}


/******************************************************************************\
 * Function:: get_strata_from_key
 *
 * @key - Key to use to get strata value
 * 
 * @int - Strata value for the given key, -1=error
 *
\******************************************************************************/
char* get_strata_from_key(int key)
{
  // Check that it is in-bounds
  if (key > strata_count)
    {
      // we were fed a bad key
      sprintf(gs, "ERROR: attempt to access out-of-range key in strata_map"  ); 
      logit(2,gs);
      
      return "-1";
    }
  else
    {
      // Return the mapped strata
      return strata_map[key];
    }
}


/******************************************************************************\
 * Function:: get_key_from_strata
 *
 * @strata - Strata to use to get key value
 * 
 * @int - Key value for the given strata, -1=error
 *
\******************************************************************************/
int get_key_from_strata(char* strata)
{
    int key = -1;
    int i = 0;
      
    // Loop through all the entries to see if we get a strata match
    for (i=0;i<strata_count;i++)
    {
        if (strcmp(strata,strata_map[i]) == 0)
        {
            // We have found a pre-existing strata
            key = i;
        }      
    }
  
    // Return the result, -1 if no key found
    return key;
}


/******************************************************************************\
 * Function:: dump_strata_array
 *
 * @void - No input
 * 
 * @int - Number of records dumped
 *
\******************************************************************************/
int dump_strata_array()
{
  int i = 0;

  printf("+++++++++++++++++\n");
  printf("Strata Array Dump - strata_count = %d\n",strata_count);
  printf("-----------------\n");
  for (i=0;i<strata_count;i++)
    {
      printf("strata_map[%d]=%s\n",i,strata_map[i]);
    }
  printf("+++++++++++++++++\n");
  return i;
}


/******************************************************************************\
 * Function:: read_in_pat_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_pat_file(char* fname)
{
  FILE *fin;
  int fscanf_line = EOF;
  int i;
  int new_poly, new_rx;
  float new_acres;
  char new_ownership[64];
  char new_strata[64];
  char* zero = "0";
  char* curr_field;
  char col_header[MAX_STR_LENGTH];

  if ((fin = fopen(fname, "r")) == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    exit(1);
  }
  
  // Now to read it in...

  //while ((fscanf_line = fscanf(fin,"%d,%f,%s ,%d,%d",
  //				&new_poly, &new_acres, new_ownership, &new_strata, &new_rx)) != EOF)
  while (fgets( col_header, MAX_STR_LENGTH, fin))
  {
    curr_field = strtok( col_header, ",");
    char keys[] = " ";
    for ( i = 0; i < 5; i++ )
    {    
      switch(i)
      {
        case 0: new_poly = atoi( curr_field ); break;
        case 1: new_acres = atof( curr_field ); break;
        case 2: strncpy( new_ownership, curr_field, strcspn( curr_field, keys )); 
                new_ownership[strcspn( curr_field, keys )] = '\0'; 
                break;
        case 3: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); 
                new_strata[strcspn( curr_field, keys )] = '\0'; 
                break;
        case 4: new_rx = atoi( curr_field ); break;
      }
      curr_field = strtok( NULL, ",");
    }
        
        
      // DEBUG CODE ////////////////////////////////////////////////
      //printf("Got here Record %d = %f, %s, %d, %d\n",
      //     new_poly,new_acres,new_ownership,new_strata,new_rx);
      // DEBUG CODE ////////////////////////////////////////////////

      // check if we got a header row
    if ( new_poly == 0 && new_strata == zero && new_rx == 0 )
	{
	  // chomp it up
	  printf( "pat file header row found\n" ); 
	  continue;
	}

    
    if (new_poly <= NPOLY)
    {
	  // Sanity checks
	  if (new_rx > NPX)
	  {
	    printf("We have an out of range RX = %d\n",new_rx);
	    printf("Record %d = %s,%d,%f,%s\n",
		    new_poly,new_ownership,new_rx,new_acres,new_strata);
	  }
	  if (new_acres > 10000)
	  {
	    printf("We have an acreage over 10000 => %f\n",new_acres);
	    printf("Record %d = %s,%d,%f,%s\n",
		    new_poly,new_ownership,new_rx,new_acres,new_strata);
	  }
	  // if (new_strata > NSTRATA || new_strata < -1)
	  // {
	    // printf("We have an out of range Strata = %d\n",new_strata);
	    // printf("Record %d = %s,%d,%f,%s\n",
		    // new_poly,new_ownership,new_rx,new_acres,new_strata);
	  // }
      strcpy((char*)own_type[new_poly],(char*)new_ownership);

	  //printf("Poly: %i (%s)\n", new_poly, own_type[new_poly]);

      poly_biz_px[new_poly] = new_rx;
      acres[new_poly] = new_acres;
	  if (strcmp(new_strata,"-1") == 0)
	  {
        strcpy(strata_link[new_poly],"1");
	  }
	  else
	  {
        strcpy(strata_link[new_poly],new_strata);
	  }




	  // DEBUG CODE ////////////////////////////////////////////////
      	  //printf("Got here too! Record %d = %s,%d,%f,%d\n",
      	  //	 new_poly,own_type[new_poly],poly_biz_px[new_poly],acres[new_poly],strata_link[new_poly]);
	  // DEBUG CODE ////////////////////////////////////////////////
    }
    else
    {
      // We have a problem...
      printf("We have a problem... the poly id is > NPOLY\n");
    }
  }

  // DEBUG CODE ////////////////////////////////////////////////
  // Print out the first twenty
  //for (i=1;i<=20;i++)
  //  {
  //    printf("Record %d = %s,%d,%f,%d\n",
  //	     i,own_type[i],poly_biz_px[i],acres[i],strata_link[i]);
  //  }
  // DEBUG CODE ////////////////////////////////////////////////
  
  fclose(fin);
  return 1;
}


/******************************************************************************\
 * Function:: dump_cut_array
 *
 * @void - No input
 * 
 * @int - Number of records dumped
 *
\******************************************************************************/
int dump_cut_array()
{
  int i,ii,iii,iiii = 0;

  printf("+++++++++++++++++\n");
  printf("Cut Array Dump - \n");
  printf("-----------------\n");
  for (i=0;i<NPX;i++)
    {
      for (iii=0;iii<NSTRATA_MAP;iii++)
	{
	  for (ii=0;ii<NOFF;ii++)
	    {
	      for (iiii=0;iiii<NTP;iiii++)
		{
		  printf("x_cutbfvol[%d][%d][%d][%d]=%f\t",iii,i,ii,iiii,x_cutbfvol[iii][i][ii][iiii]);
          if (cubic_data == 0) 
          {
            printf("x_cutcubvol[%d][%d][%d][%d]=%f\n",iii,i,ii,iiii,x_cutcubvol[iii][i][ii][iiii]);
          }
		}
	    }
	}
    }
  printf("+++++++++++++++++\n");
  return i;
}

/******************************************************************************\
 * Function:: get_species_index
 *
 * @void - species name (string)
 * 
 * @int - The numeric identifier for that species
 *
\******************************************************************************/
int get_species_index( char* species_string )
{
  int i = 0;
  for ( i = 0; i < species_count; i++ )
    {
      if ( strcmp((char*)species_map[i], species_string ) == 0 )
	{
	  return i;
	}
    }

  if ( species_count == NSPECIES )
    {
      sprintf(gs, "WARNING: number of species found exceeds NSPECIES" ); 
      logit(2,gs);
      return 0;
    }

  strcpy( species_map[ species_count ], species_string );
  //printf( "recording new species code: %s\n", species_string, species_map[species_count] );
  species_count++;

  return species_count - 1;
}


/******************************************************************************\
 * Function:: read_in_cut_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_cut_file(char* fname)
{
    FILE *fin;
    int fscanf_line = EOF;
    int i;
    int new_rx, new_offset, new_tp;
    float new_cutvol;
    int new_strata_key = -1;
    int lines_processed = 0;
    char col_header[MAX_STR_LENGTH];
    char new_species[MAX_STR_LENGTH];
    char new_strata[64];
    char* zero = "0";
    char * curr_field;
    
    int sk, offset, tp, rx;
    int prev_cut_offset;

    // Initialize the cut buffer to zero...
    memset(x_cutbfvol,     0,   sizeof(x_cutbfvol));
    memset(x_cutbfvol_valid,     0,   sizeof(x_cutbfvol_valid));
      

    // Check that the file is valid
    if ((fin = fopen(fname, "r")) == NULL) {
      fprintf(stderr, "Unable to open file %s\n", fname);
      exit(1);
    }
  
  // Now to read it in...
  //while ((fscanf_line = fscanf(fin,"%d,%d,%d,%d,%s ,%f,%s",
//				&new_rx, &new_offset, &new_strata, &new_tp, new_species, &new_cutvol, read_buffer )) != EOF)
    while (fgets( col_header, MAX_STR_LENGTH, fin))
    {
        curr_field = strtok( col_header, ",");
        char keys[] = " ";
        
        for ( i = 0; i < 6; i++ )
        {    
            switch(i)
            {
                case 0: new_rx = atoi( curr_field ); break;
                case 1: new_offset = atoi( curr_field ); break;
                case 2: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); new_strata[strcspn( curr_field, keys )] = '\0'; break;
                case 3: new_tp = atoi( curr_field ); break;
                case 4: strncpy( new_species, curr_field, strcspn( curr_field, keys )); new_species[strcspn( curr_field, keys )] = '\0'; break;
                case 5: new_cutvol = atof( curr_field ); break;
            }
            curr_field = strtok( NULL, ",");
        }
    
        // check if we got a header row
        if ( new_rx == 0 && new_offset == 0 && new_strata == zero && new_tp == 0 )
        {
          // chomp it up
          printf( "cut file header found\n" ); 
          continue;
        }

        //printf("Record %d,%f\n", new_strata, new_cutvol);
        // DEBUG CODE ////////////////////////////////////////////////      
        /*if (new_cutvol == 0)
        {
          printf("%s, %f\n", new_species, new_cutvol);
        }*/
        //printf("Record %d = %s,%d,%f,%d\n", new_rx,new_strata);
        // DEBUG CODE ////////////////////////////////////////////////
      
        if (new_rx <= NPX &&
            new_offset <= NOFF &&
            // new_strata <= NSTRATA &&
            new_tp <= NTP)
        {
            lines_processed++;
            new_strata_key = load_new_strata(new_strata);
    
          // DEBUG CODE ////////////////////////////////////////////////
          //printf("New Line %d \n",lines_processed);
          //printf("x_cutbfvol[%d][%d][%d][%d] = %d \n",new_strata_key,new_rx,new_offset,new_tp,&new_cutvol);    
          // DEBUG CODE ////////////////////////////////////////////////

            if (new_strata_key == -1)
            {
                printf("We have a problem... strata key = -1\n");
            }

            if ( strcmp( new_species, "total" ) == 0 )
            {
                if ( x_cutbfvol[new_strata_key][new_rx][new_offset-1][new_tp] > 0.0 )
                {
                    sprintf(gs,"WARNING: multiple cut rows for rx %d, off %d, plot %s, tp %d", new_rx, new_offset, new_strata, new_tp);
                    logit(2,gs);
                }

                x_cutbfvol[new_strata_key][new_rx][new_offset-1][new_tp] += (double)new_cutvol;    
                x_cutbfvol_valid[new_strata_key][new_rx][new_offset-1][new_tp] = 1;

                  // DEBUG CODE ////////////////////////////////////////////////
                //printf("x_cutbfvol[%d][%d][%d][%d] = %f %f \n",new_strata_key,new_rx,new_offset-1,new_tp,
                //    new_cutvol,x_cutbfvol[new_strata_key][new_rx][new_offset-1][new_tp]);    
                  // DEBUG CODE ////////////////////////////////////////////////
            }
            else // per-species cut info
            {
                // find the index for this species
                int spec_index = get_species_index( new_species );
                  
                x_cutbfvol_spec[new_strata_key][new_rx][new_offset-1][new_tp][spec_index] += (double)new_cutvol;    
            }
      	}
        else
      	{
            // We have a problem...
            if ( new_rx > NPX )
            {
                sprintf(gs,"WARNING: rx out of range: %d (%d, %d, %s, %d, %f)", new_rx,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
          
            if ( new_offset > NOFF )
            {
                sprintf(gs,"WARNING: offset out of range: %d (%d, %d, %s, %d, %f)", new_offset,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
            
            // if ( new_strata > NSTRATA )
            // {
                // sprintf(gs,"WARNING: plot ID out of range: %d (%d, %d, %d, %d, %f)", new_strata,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                // logit(2,gs);
            // }
            
            if ( new_tp > NTP )
            {
                sprintf(gs,"WARNING: tp out of range: %d (%d, %d, %s, %d, %f)", new_tp,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
        }
    }

    // sanity check on incoming data: make sure cuts are spread over offset
    for ( sk = 0; sk <= NSTRATA_MAP; sk++ )
    {
        for ( rx = 0; rx <= NPX; rx++ )
        {
            for ( tp = 0; tp <= NTP; tp++ )
            {
                prev_cut_offset = -1;
                for ( offset = 0; offset <= NOFF; offset++ )
                {
                    if ( x_cutbfvol[sk][rx][offset][tp] > 0.0 )
                    {
                        if (( prev_cut_offset >= 0 && prev_cut_offset == offset - 1 )
                            && (tp > 0 && x_cutbfvol[sk][rx][prev_cut_offset][tp-1] < 0.00000001)) // if prev offset had cuts 2 tps in a row, no error here
                        {
                            // sprintf(gs, "WARNING: cuts made in consecutive offsets! st: %s, rx: %i, tp: %i, off: %i", strata_map[sk], rx, tp, offset );
                            // logit(2,gs);
                            // printf("   (prev: st: %s, rx:%i, tp: %i, prev_off: %i off: %i, cutbfvol = %f)\n", strata_map[sk], rx, tp, prev_cut_offset, offset, x_cutbfvol[sk][rx][prev_cut_offset][tp-1] );
                        }
                        prev_cut_offset = offset;
                    }  
                }
            }
        }
    }

    sprintf(gs,"%d Lines Processed from Cut File",lines_processed);
    logit(2,gs);
    fclose(fin);
    return 1;
}


/******************************************************************************\
 * Function:: read_in_cut_cu_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_cut_cu_file(char* fname)
{
    FILE *fin;
    int fscanf_line = EOF;
    int i;
    int new_rx, new_offset, new_tp;
    float new_cutvol;
    int new_strata_key = -1;
    int lines_processed = 0;
    char col_header[MAX_STR_LENGTH];
    char new_species[MAX_STR_LENGTH];
    char new_strata[64];
    char* zero = "0";
    char * curr_field;

    // Check that the file is valid
    if ((fin = fopen(fname, "r")) == NULL) {
      fprintf(stderr, "Unable to open file %s\n", fname);
      cubic_data = 1;
      return 1;
    }
    
    cubic_data = 0;
    
    // Initialize the cut buffer to zero...
    memset(x_cutcubvol,     0,   sizeof(x_cutcubvol));
    memset(x_cutcubvol_valid,     0,   sizeof(x_cutcubvol_valid));
        
  // Now to read it in...
    while (fgets( col_header, MAX_STR_LENGTH, fin))
    {
        curr_field = strtok( col_header, ",");
        char keys[] = " ";
        
        for ( i = 0; i < 6; i++ )
        {    
            switch(i)
            {
                case 0: new_rx = atoi( curr_field ); break;
                case 1: new_offset = atoi( curr_field ); break;
                case 2: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); new_strata[strcspn( curr_field, keys )] = '\0'; break;
                case 3: new_tp = atoi( curr_field ); break;
                case 4: strncpy( new_species, curr_field, strcspn( curr_field, keys )); new_species[strcspn( curr_field, keys )] = '\0'; break;
                case 5: new_cutvol = atof( curr_field ); break;
            }
            curr_field = strtok( NULL, ",");
        }
    
        // check if we got a header row
        if ( new_rx == 0 && new_offset == 0 && new_strata == zero && new_tp == 0 )
        {
          // chomp it up
          printf( "cubic cut file header found\n" ); 
          continue;
        }

        //printf("Record %d,%f\n", new_strata, new_cutvol);
        // DEBUG CODE ////////////////////////////////////////////////      
        /*if (new_cutvol == 0)
        {
          printf("%s, %f\n", new_species, new_cutvol);
        }*/
        //printf("Record %d = %s,%d,%f,%d\n", new_rx,new_strata);
        // DEBUG CODE ////////////////////////////////////////////////
      
        if (new_rx <= NPX &&
            new_offset <= NOFF &&
            // new_strata <= NSTRATA &&
            new_tp <= NTP)
        {
            lines_processed++;
            new_strata_key = load_new_strata(new_strata);
    
          // DEBUG CODE ////////////////////////////////////////////////
          //printf("New Line %d \n",lines_processed);
          //printf("x_cutcubvol[%d][%d][%d][%d] = %d \n",new_strata_key,new_rx,new_offset,new_tp,&new_cutvol);    
          // DEBUG CODE ////////////////////////////////////////////////

            if (new_strata_key == -1)
            {
                printf("We have a problem... strata key = -1\n");
            }

            if ( strcmp( new_species, "total" ) == 0 )
            {
                if ( x_cutcubvol[new_strata_key][new_rx][new_offset-1][new_tp] > 0.0 )
                {
                    sprintf(gs,"WARNING: multiple cubic cut rows for rx %d, off %d, plot %s, tp %d", new_rx, new_offset, new_strata, new_tp);
                    logit(2,gs);
                }

                x_cutcubvol[new_strata_key][new_rx][new_offset-1][new_tp] += (double)new_cutvol;    
                x_cutcubvol_valid[new_strata_key][new_rx][new_offset-1][new_tp] = 1;

                  // DEBUG CODE ////////////////////////////////////////////////
                //printf("x_cutcubvol[%d][%d][%d][%d] = %f %f \n",new_strata_key,new_rx,new_offset-1,new_tp,
                //    new_cutvol,x_cutcubvol[new_strata_key][new_rx][new_offset-1][new_tp]);    
                  // DEBUG CODE ////////////////////////////////////////////////
            }
            else // per-species cut info
            {
                // find the index for this species
                int spec_index = get_species_index( new_species );
                  
                x_cutcubvol_spec[new_strata_key][new_rx][new_offset-1][new_tp][spec_index] += (double)new_cutvol;    
            }
      	}
        else
      	{
            // We have a problem...
            if ( new_rx > NPX )
            {
                sprintf(gs,"WARNING: rx out of range: %d (%d, %d, %s, %d, %f)", new_rx,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
          
            if ( new_offset > NOFF )
            {
                sprintf(gs,"WARNING: offset out of range: %d (%d, %d, %s, %d, %f)", new_offset,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
            
            // if ( new_strata > NSTRATA )
            // {
                // sprintf(gs,"WARNING: plot ID out of range: %d (%d, %d, %d, %d, %f)", new_strata,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                // logit(2,gs);
            // }
            
            if ( new_tp > NTP )
            {
                sprintf(gs,"WARNING: tp out of range: %d (%d, %d, %s, %d, %f)", new_tp,new_rx,new_offset,new_strata,new_tp,new_cutvol);
                logit(2,gs);
            }
        }
    }

    // sanity check on incoming data: make sure cuts are spread over offset
    int sk, offset, tp, rx;
    for ( sk = 0; sk <= NSTRATA_MAP; sk++ )
    {
        for ( rx = 0; rx <= NPX; rx++ )
        {
            for ( tp = 0; tp <= NTP; tp++ )
            {
                int prev_cut_offset = -1;
                for ( offset = 0; offset <= NOFF; offset++ )
                {
                    if ( x_cutcubvol[sk][rx][offset][tp] > 0.0 )
                    {
                        if (( prev_cut_offset >= 0 && prev_cut_offset == offset - 1 )
                            && (tp > 0 && x_cutcubvol[sk][rx][prev_cut_offset][tp-1] < 0.00000001)) // if prev offset had cuts 2 tps in a row, no error here
                        {
                            sprintf(gs, "WARNING: cuts made in consecutive offsets! st: %s, rx: %i, tp: %i, off: %i", strata_map[sk], rx, tp, offset );
                            logit(2,gs);
                            //printf("   (prev: st: %i, rx:%i, tp: %i, off: %i)\n", strata_map[sk], rx, tp, prev_cut_offset );
                        }
                        prev_cut_offset = offset;
                    }  
                }
            }
        }
    }

    sprintf(gs,"%d Lines Processed from Cubic Cut File",lines_processed);
    logit(2,gs);
    fclose(fin);
    return 1;
}


/******************************************************************************\
 * Function:: read_in_car_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_car_file(char* fname)
{
  FILE *fin;
  int fscanf_line = EOF;
  int i;
  int new_rx, new_offset, new_tp;
  float new_carbon;
  int new_strata_key = -1;
  int lines_processed = 0;
  char col_header[MAX_STR_LENGTH];
  char new_strata[64];
  char* zero = "0";
  char * curr_field;

  // Initialize the carbon buffer to zero...
  memset(x_C_tons,     0,   sizeof(x_C_tons));
  

  // Check that the file is valid
  if ((fin = fopen(fname, "r")) == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    return 0;
  }
  
  // Now to read it in...
  //while ((fscanf_line = fscanf(fin,"%d,%d,%d,%d,%f,%s",
	//			&new_rx, &new_offset, &new_strata, &new_tp, &new_carbon, read_buffer)) != EOF)
  while (fgets( col_header, MAX_STR_LENGTH, fin))
  {
    curr_field = strtok( col_header, ",");
    char keys[] = " ";
    for ( i = 0; i < 5; i++ )  
    {    
      switch(i)
      {
        case 0: new_rx = atoi( curr_field ); break;
        case 1: new_offset = atoi( curr_field ); break;
        case 2: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); new_strata[strcspn( curr_field, keys )] = '\0'; break;
        case 3: new_tp = atoi( curr_field ); break;
        case 4: new_carbon = atof( curr_field ); break;
    
      }
            curr_field = strtok( NULL, ",");
    }
        
    // check if we got a header row
    if ( new_rx == 0 && new_offset == 0 && new_strata == zero && new_tp == 0 )
	{
	  // chomp it up
	  printf( "carbon file header found\n" ); 
	  continue;
	}

            
    if (new_rx <= NPX &&
	  new_offset <= NOFF &&
	  // new_strata <= NSTRATA &&
	  new_tp <= NTP)
    {
	  lines_processed++;
	  new_strata_key = load_new_strata(new_strata);
    
	  if (new_strata_key == -1)
	  {
	    printf("We have a problem... strata key = -1\n");
	  }

	  if ( x_C_tons[new_strata_key][new_rx][new_offset-1][new_tp] > 0.0 )
	  {
	    sprintf(gs,"WARNING: multiple carbon rows for rx %d, off %d, plot %s, tp %d", new_rx, new_offset, new_strata, new_tp);
	    logit(2,gs);
	  }
	  x_C_tons[new_strata_key][new_rx][new_offset-1][new_tp] += (double)new_carbon;    

    }
    else
    {
      // We have a problem...
	  if ( new_rx > NPX ){
	    sprintf(gs,"WARNING: rx out of range: %d (%d, %d, %s, %d, %f)", new_rx,new_rx,new_offset,new_strata,new_tp,new_carbon);
	    logit(2,gs);
	  }
	  if ( new_offset > NOFF )
      {
	    sprintf(gs,"WARNING: offset out of range: %d (%d, %d, %s, %d, %f)", new_offset,new_rx,new_offset,new_strata,new_tp,new_carbon);
	    logit(2,gs);
	  }
	  // if ( new_strata > NSTRATA )
      // {
	    // sprintf(gs,"WARNING: plot ID out of range: %d (%d, %d, %d, %d, %f)", new_strata,new_rx,new_offset,new_strata,new_tp,new_carbon);
	    // logit(2,gs);
	  // }
	  if ( new_tp > NTP )
      {
	    sprintf(gs,"WARNING: tp out of range: %d (%d, %d, %s, %d, %f)", new_tp,new_rx,new_offset,new_strata,new_tp,new_carbon);
	    logit(2,gs);
	  }
   	}
  }

  sprintf(gs,"%d Lines Processed from Carbon File",lines_processed);
  logit(2,gs);
  fclose(fin);
  return 1;
}

/******************************************************************************\
 * Function:: read_in_age_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_age_file(char* fname)
{
  FILE *fin;
  int fscanf_line = EOF;
  int i;
  int new_rx, new_offset, new_tp, new_age;  
  int new_strata_key = -1;
  int lines_processed = 0;
  char col_header[MAX_STR_LENGTH];
  char new_strata[64];
  char* zero = "0";
  char * curr_field;

  // Initialize the age buffer to zero...
  memset(x_age,     0,   sizeof(x_age));

  // Check that the file is valid
  if ((fin = fopen(fname, "r")) == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    return 0;
  }
  
  // Now to read it in...
  while (fgets( col_header, MAX_STR_LENGTH, fin))
  {
    curr_field = strtok( col_header, ",");
    char keys[] = " ";
    for ( i = 0; i < 5; i++ )   
    {    
      switch(i)
      {
        case 0: new_rx = atoi( curr_field ); break;
        case 1: new_offset = atoi( curr_field ); break;
        case 2: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); new_strata[strcspn( curr_field, keys )] = '\0'; break;
        case 3: new_tp = atoi( curr_field ); break;
        case 4: new_age = atoi( curr_field ); break;
      }
      curr_field = strtok( NULL, ",");
    }
        
    // check if we got a header row
    if ( new_rx == 0 && new_offset == 0 && new_strata == zero && new_tp == 0 )
	{
	  // chomp it up
	  printf( "age file header found\n" ); 
	  continue;
	}
           
    if (new_rx <= NPX &&
	  new_offset <= NOFF &&
	  // new_strata <= NSTRATA &&
	  new_tp <= NTP &&
      new_age <= ADVANCED_AGE &&
      new_age >= YOUNG_AGE)
    {
	  lines_processed++;
	  new_strata_key = load_new_strata(new_strata);
    
	  if (new_strata_key == -1)
	  {
	    printf("We have a problem... strata key = -1\n");
	  }

	  if ( x_age[new_strata_key][new_rx][new_offset-1][new_tp] > 0.0 )
	  {
	    sprintf(gs,"WARNING: multiple age rows for rx %d, off %d, plot %s, tp %d", new_rx, new_offset, new_strata, new_tp);
	    logit(2,gs);
	  }
	  x_age[new_strata_key][new_rx][new_offset-1][new_tp] = new_age;  

    }
    else
    {
      // We have a problem...
	  if ( new_rx > NPX )
      {
	    sprintf(gs,"WARNING: rx out of range: %d (%d, %d, %s, %d, %f)", new_rx,new_rx,new_offset,new_strata,new_tp,new_age);
	    logit(2,gs);
	  }
	  if ( new_offset > NOFF )
      {
	    sprintf(gs,"WARNING: offset out of range: %d (%d, %d, %s, %d, %f)", new_offset,new_rx,new_offset,new_strata,new_tp,new_age);
	    logit(2,gs);
	  }
	  // if ( new_strata > NSTRATA )
      // {
	    // sprintf(gs,"WARNING: plot ID out of range: %d (%d, %d, %d, %d, %f)", new_strata,new_rx,new_offset,new_strata,new_tp,new_age);
	    // logit(2,gs);
	  // }
	  if ( new_tp > NTP )
      {
	    sprintf(gs,"WARNING: tp out of range: %d (%d, %d, %s, %d, %f)", new_tp,new_rx,new_offset,new_strata,new_tp,new_age);
	    logit(2,gs);
	  }
      if ( new_age < YOUNG_AGE || new_age > ADVANCED_AGE )
      {
        sprintf(gs,"WARNING: age out of range: %d (%d, %d, %s, %d, %f)", new_age,new_rx,new_offset,new_strata,new_tp,new_age);
        logit(2,gs);
      }
    }
  }

  sprintf(gs,"%d Lines Processed from Age File",lines_processed);
  logit(2,gs);
  fclose(fin);
  return 1;
}

/******************************************************************************\
 * Function:: read_in_live_file
 *
 * @fname - File to read in
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int read_in_live_file(char* fname)
{
  FILE *fin;
  int fscanf_line = EOF;
  int i;
  int new_rx, new_offset, new_tp;
  float new_live;
  int new_strata_key = -1;
  int lines_processed = 0;
  char col_header[MAX_STR_LENGTH];
  char new_strata[64];
  char* zero = "0";
  char * curr_field;

  // Initialize the carbon buffer to zero...
  memset(x_livevol,     0,   sizeof(x_livevol));
  

  // Check that the file is valid
  if ((fin = fopen(fname, "r")) == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    return 0;
  }
  
  // Now to read it in...
  //while ((fscanf_line = fscanf(fin,"%d,%d,%d,%d,%f,%s",
//				&new_rx, &new_offset, &new_strata, &new_tp, &new_live, read_buffer)) != EOF)
  while (fgets( col_header, MAX_STR_LENGTH, fin))
  {
        curr_field = strtok( col_header, ",");
        char keys[] = " ";
        for ( i = 0; i < 5; i++ )
        {    
            switch(i)
            {
                case 0: new_rx = atoi( curr_field ); break;
                case 1: new_offset = atoi( curr_field ); break;
                case 2: strncpy( new_strata, curr_field, strcspn( curr_field, keys )); new_strata[strcspn( curr_field, keys )] = '\0'; break;
                case 3: new_tp = atoi( curr_field ); break;
                case 4: new_live = atof( curr_field ); break;
            }
            curr_field = strtok( NULL, ",");
        }
        
      // check if we got a header row
      if ( new_rx == 0 && new_offset == 0 && new_strata == zero && new_tp == 0 )
	{
	  // chomp it up
	  printf( "live file header found\n" ); 
	  continue;
	}

            
      if (new_rx <= NPX &&
	  new_offset <= NOFF &&
	  // new_strata <= NSTRATA &&
	  new_tp <= NTP)
      	{
	  lines_processed++;
	  new_strata_key = load_new_strata(new_strata);
    
	  if (new_strata_key == -1)
	    {
	      printf("We have a problem... strata key = -1\n");
	    }

	  if ( x_livevol[new_strata_key][new_rx][new_offset-1][new_tp] > 0.0 )
	    {
	      sprintf(gs,"WARNING: multiple live rows for rx %d, off %d, plot %s, tp %d", new_rx, new_offset, new_strata, new_tp);
	      logit(2,gs);
	    }
	  x_livevol[new_strata_key][new_rx][new_offset-1][new_tp] += (double)new_live;    

      	}
      else
      	{
      	  // We have a problem...
	  if ( new_rx > NPX ){
	    sprintf(gs,"WARNING: rx out of range: %d (%d, %d, %s, %d, %f)", new_rx,new_rx,new_offset,new_strata,new_tp,new_live);
	    logit(2,gs);
	  }
	  if ( new_offset > NOFF ){
	    sprintf(gs,"WARNING: offset out of range: %d (%d, %d, %s, %d, %f)", new_offset,new_rx,new_offset,new_strata,new_tp,new_live);
	    logit(2,gs);
	  }
	  // if ( new_strata > NSTRATA ){
	    // sprintf(gs,"WARNING: plot ID out of range: %d (%d, %d, %d, %d, %f)", new_strata,new_rx,new_offset,new_strata,new_tp,new_live);
	    // logit(2,gs);
	  // }
	  if ( new_tp > NTP ){
	    sprintf(gs,"WARNING: tp out of range: %d (%d, %d, %s, %d, %f)", new_tp,new_rx,new_offset,new_strata,new_tp,new_live);
	    logit(2,gs);
	  }
      	}
    }

  sprintf(gs,"%d Lines Processed from Live File",lines_processed);
  logit(2,gs);
  fclose(fin);
  return 1;
}


/******************************************************************************\
 * Function:: harvest
 *
 * @ownership - Ownership type we are processing for in this call.
 * @target_value - Target cut volume (per time period) for the
 *                 ownership type.                            
 * 
 * @void - No return value
 *
\******************************************************************************/
void harvest(int alt_biz, char* ownership, double target_val, double boost_percent, int boost_periods, int first_boost_period)
{

  FILE *fin;

  int k,k1,k2,adj_poly,sta_key,pxa,offset,offadj,poffset;
  int px,st_key;
  char* st;
  char* sta;
  char* zero = "0";
  double obj,temp_obj,best_obj, temp_carbon;
  double delta,m1;
  double change;
  int obj_it = 0;
  int obj_it_rand = 0;
  int temp_change_it = 0;
  int obj_no_change = 0;

  int tp;
  int spec;
  int n_trials = 0;
  int i;
  int rep,nrep;
  int cand_poly;
  double target_vol[NTP+1];  
  float temp,alpha,end_temp,x,ex;		
  float vol_per_period[NTP+1];
  float spec_vol_per_period[NTP+1][NSPECIES];
  float cub_vol_per_period[NTP+1];
  float spec_cub_vol_per_period[NTP+1][NSPECIES];
  float obj_per_period[NTP+1];
  float carbon_per_period[NTP+1];
  float livevol_per_period[NTP+1];
  float vol_per_period_check[NTP+1][NOFF+1];
  float cub_vol_per_period_check[NTP+1][NOFF+1];
  float carbon_per_period_check[NTP+1][NOFF+1];
  float livevol_per_period_check[NTP+1][NOFF+1];
  //float inv_per_period[NTP+1];
  int soln[NPOLY+1];
  int soln_modified[NPOLY+1];
  

  // Added by APR
  char out_file_txt[MAX_STR_LENGTH];
  char out_file_summary[MAX_STR_LENGTH];
  double volume_total = 0.0;

  int debug_count1 = 0;
  int debug_count2 = 0;
  int debug_count3 = 0;
  int cub_debug_count1 = 0; //for the addition of cubic cut vol entries
  int cub_debug_count2 = 0;
  int index1 = 0;
  
  // Added by RDH for Age consideration
  double total_acres = 0;
  double advanced_acres[NTP+1];
  // int prev_offset[NPOLY+1][NTP+1];
  int (*prev_offset)[NTP+1];
  prev_offset = (int (*)[NTP+1]) malloc(sizeof(int) * (NPOLY+1) * (NTP+1));
  
  if (alt_biz == 0)
  {
    //sprintf(out_file_txt,"output_%s.txt",ownership);
    sprintf(out_file_txt,"./data/bus_sch.txt");
    sprintf(out_file_summary,"./data/bus_summary.txt");
  }
  else
  {
    sprintf(out_file_txt,"./data/alt_sch.txt");
    sprintf(out_file_summary,"./data/alt_summary.txt");
  }

  // DEBUG CODE ////////////////////////////////////////////////
  //dump_strata_array();
  //dump_cut_array();
  // DEBUG CODE ////////////////////////////////////////////////

  srand(1);    // initialize random number seed
  
  m1=10.0;

  
  //=====================================================
  // initial solution
  //=====================================================
  
  memset(vol_per_period,     0,   sizeof(vol_per_period));
  for ( i = 0; i < NTP+1; i++ )
  {
    vol_per_period[i] = 0.f;
  }
  
  memset(cub_vol_per_period,     0,   sizeof(cub_vol_per_period));
  for ( i = 0; i < NTP+1; i++ )
  {
    cub_vol_per_period[i] = 0.f;
  }
  
  memset(vol_per_period_check,     0,   sizeof(vol_per_period_check)); 
  memset(cub_vol_per_period_check,     0,   sizeof(cub_vol_per_period_check));
  memset(spec_vol_per_period,    0,  sizeof(spec_vol_per_period));
  memset(spec_cub_vol_per_period,    0,  sizeof(spec_cub_vol_per_period));
  memset(obj_per_period,     0,   sizeof(obj_per_period));
  memset(carbon_per_period,     0,   sizeof(carbon_per_period));
  memset(carbon_per_period_check,     0,   sizeof(carbon_per_period_check));
  memset(livevol_per_period,     0,   sizeof(livevol_per_period));
  memset(livevol_per_period_check,     0,   sizeof(livevol_per_period_check));
  memset(advanced_acres,     0,   sizeof(advanced_acres));
  memset(prev_offset,   0,  sizeof(prev_offset));
  
  // DEBUG CODE ////////////////////////////////////////////////
  // Added by APR to put in dummy init value
  //  for (i=1;i<=NPOLY;i++)
  //    {
  //      if (i%2 == 0)
  //	{
  //	  strcpy((char*)own_type[i],"STATE");
  //	}
  //      else
  //	{
  //	  strcpy((char*)own_type[i],"FEDERAL");
  //	}
  //      beg_adj_ptr[i] = (i-1) * 5;
  //      end_adj_ptr[i] = ((i-1) * 5) + 4;
  //    }
  //  for (i=1;i<=(sizeof(adj_list)/sizeof(int))-1;i++)
  //    {
  //      adj_list[i] = (rand() % NPOLY) + 1;
  //    } 
  //  for (i=1;i<=(sizeof(strata_link)/sizeof(int))-1;i++)
  //    {
  //      strata_link[i] = (rand() % 5) + 1;
  //    } 
  //  for (i=1;i<=(sizeof(poly_biz_px)/sizeof(int))-1;i++)
  //    {
  //      poly_biz_px[i] = 1;
  //    } 
  // DEBUG CODE ////////////////////////////////////////////////
  
  
  sprintf(gs, "---------------------------------------------------");  logit(1,gs);
  sprintf(gs, "---------------------------------------------------");  logit(1,gs);
  sprintf(gs, "           PROCESSING %s",ownership);  logit(1,gs);
  sprintf(gs, "---------------------------------------------------");  logit(1,gs);
  sprintf(gs, "---------------------------------------------------");  logit(1,gs);

  for (i=1;i<=NPOLY;i++)
  {
    // Init the offset array to be 0 by default
    soln[i]=0;
    soln_modified[i]=0;
    // DEBUG CODE ////////////////////////////////////////////////
    //sprintf(gs, "soln[%d]=%d",i,soln[i]);
    //logit(1,gs);
    // DEBUG CODE ////////////////////////////////////////////////
    total_acres += acres[i];
    if (strcmp(own_type[i],ownership)!=0) goto skipcount;
      
    st=strata_link[i];


    // if (st==zero) goto skipcount; // not a forest poly
    if (strcmp(st,zero) == 0) goto skipcount; // not a forest poly
      
    st_key = get_key_from_strata(st);
    if (st_key == -1) 
    {
      // warning to log file if key not found
      sprintf(gs, "WARNING: could not locate strata %s in strata_map! (appears in pat file, but not others)", st ); 
      logit(2,gs);
      goto skipcount; // poly's strata had no cut, live, or carbon data
    }
      
    px=poly_biz_px[i];
    
    // Init the offset to 0 (we are zero based even though the file is 1 based)
    offset=0;
      
    for (tp=0;tp<=NTP;tp++)
	{
    //this calculation is because volumes are input as bf over the period (5 years)
    //and we want mmbf per year, so we divide by 5,000,000 - if period length 
    //changes this value needs to change

	  vol_per_period[tp]+= (x_cutbfvol[st_key][px][offset][tp]*acres[i])/TO_MMBFPY_DENOM;  
      if (cubic_data == 0) 
      {
        cub_vol_per_period[tp]+= (x_cutcubvol[st_key][px][offset][tp]*acres[i])/TO_MMCUBFPY_DENOM;  
      }
	  carbon_per_period[tp]+= (x_C_tons[st_key][px][offset][tp]*acres[i]);  
	  livevol_per_period[tp]+= (x_livevol[st_key][px][offset][tp]*acres[i])/TO_MMBFPY_DENOM_LIVE;  

	  for ( spec=0;spec<NSPECIES;spec++ )
	  {
	    spec_vol_per_period[tp][spec] += (x_cutbfvol_spec[st_key][px][offset][tp][spec]*acres[i])/TO_MMBFPY_DENOM;
        if (cubic_data == 0) 
        {
          spec_cub_vol_per_period[tp][spec] += (x_cutcubvol_spec[st_key][px][offset][tp][spec]*acres[i])/TO_MMCUBFPY_DENOM; 
        }
	  }

	  // DEBUG CODE ////////////////////////////////////////////////
	  //inv_per_period[tp]+= (x_bfvol[st][px][offset][tp]*acres[i])/TO_MMBFPY_DENOM; 
	  //sprintf(gs, "tp %3d  vol  %7.4f",tp,vol_per_period[tp]);  logit(1,gs);
	  // DEBUG CODE ////////////////////////////////////////////////
	  
	  if (x_cutbfvol_valid[st_key][px][offset][tp] == 1)
	  {
	    // Count up the number of polygons we are considering...
	    debug_count1++;   
	  }
	  else
	  {
	    // We have a problem
	    debug_count2++;
	  }
        
      if (cubic_data == 0) 
      {
        if (x_cutcubvol_valid[st_key][px][offset][tp] == 1)
        {
          // Count up the number of polygons we are considering...
          cub_debug_count1++;  
        }
        else
        {
          // We have a problem
          cub_debug_count2++;
        }
      }
	  
	  for (index1=0;index1<NOFF;index1++)
	  {
	    vol_per_period_check[tp][index1]+= (x_cutbfvol[st_key][px][offset+index1][tp]*acres[i])/TO_MMBFPY_DENOM; 
        if (cubic_data == 0) 
        {
          cub_vol_per_period_check[tp][index1]+= (x_cutcubvol[st_key][px][offset+index1][tp]*acres[i])/TO_MMCUBFPY_DENOM; 
        }
	    carbon_per_period_check[tp][index1]+= (x_C_tons[st_key][px][offset+index1][tp]*acres[i]); 
	    livevol_per_period_check[tp][index1]+= (x_livevol[st_key][px][offset+index1][tp]*acres[i])/TO_MMBFPY_DENOM_LIVE; 
  	  }

      if (x_age[st_key][px][offset][tp] == ADVANCED_AGE) 
      {
        advanced_acres[tp] += acres[i];
      }
      
	}
    skipcount:;	  
  }
  
  // DEBUG CODE ////////////////////////////////////////////////
  sprintf(gs, "Number of valid entries from cut file = %d\n",debug_count1);  logit(1,gs);
  //sprintf(gs, "Number of invalid entries from the cut file = %d\n",debug_count2);  logit(1,gs);
  // DEBUG CODE ////////////////////////////////////////////////

  if ( debug_count1 == 0 )
  {
    printf( "No valid cut data found -- did you enter the right ownership code?\n" );
    exit(1);
  }
    
  if ( (debug_count1 != cub_debug_count1) && (cubic_data == 0) )
  {
    printf( "ERROR: The number of valid entries between the cut file and the cubic cut file do not match.\n" );
    exit(1);
  }

  // DEBUG CODE ////////////////////////////////////////////////
  // Use this to see the other initial offset values
  //for (index1=0;index1<NOFF;index1++)
  // DEBUG CODE ////////////////////////////////////////////////

  for (index1=0;index1<1;index1++)
  {
    volume_total = 0.0;
    sprintf(gs, "Init Cut Volume Per Period - Default Perscription and offset %d::",index1);  logit(1,gs);
    for (tp=0;tp<=NTP;tp++)
	{
	  sprintf(gs, "tp %3d  vol  %7.4f   live %7.4f   C %7.4f",tp,vol_per_period_check[tp][index1],livevol_per_period_check[tp][index1],carbon_per_period_check[tp][index1]);
	  logit(1,gs);
	  volume_total += vol_per_period_check[tp][index1];                 
	}
    sprintf(gs, "Total Cut Volume = %7.4f\n",volume_total);  logit(1,gs);
    sprintf(gs, "----------------------------------------------");  logit(1,gs);
  }
  //sprintf(gs, "---------------------------------------------------\n");  logit(1,gs);
  
  //=====================================================
  // target volumes 
  //=====================================================
  
  
  sprintf(gs, "Target Volume -> User Defined = %f",target_val);  logit(1,gs);
  target_vol[0] = 0.0;
  for (tp=1;tp<=NTP;tp++)
  {
    target_vol[tp] = target_val;   // target volume per year

    if ( tp >= first_boost_period && tp < first_boost_period + boost_periods )
    {
	  target_vol[tp] *= (100.0+boost_percent)/100.0;
    }
    //printf( "tp: %i, target vol: %f\n", tp, target_vol[tp] );
  }
  
  
  //=====================================================
  // calculate initial value of objective function
  //=====================================================
  
  obj=0.0;
  temp_carbon = 0.0;
  best_obj=0.0;
 
  for (tp=1;tp<=NTP;tp++)
  {
    obj_per_period[tp]=m1*pow(fabs(target_vol[tp]-vol_per_period[tp]),OBJ_EXPONENT);
    obj+=obj_per_period[tp];  
    temp_carbon += carbon_per_period[tp];
  } 
  
  if (CARBON_WEIGHT != 0) {
    obj = obj/(CARBON_WEIGHT * temp_carbon);
  }
  
  sprintf(gs, "Initial objective function = %7.4f",obj);
  //the obj function is ending up as "nan" so let's test the variables
  //      sprintf(gs, "target volume = %d\n",target_vol);
  //    sprintf(gs, "an vol = %d\n",vol_per_period);
  //    sprintf(gs, "and dont know what this is = %d\n",vol_per_period_check);
  logit(2,gs);
  


  //==========================================================================
  // control parameters 
  //==========================================================================
  
  temp=SA_START_TEMPERATURE;  
  nrep=SA_POLY_TESTS_PER_TEMP;
  alpha=SA_TEMP_DECAY_PER_ITER;
  end_temp=SA_MINIMUM_TEMP;
  
  // DEBUG CODE ////////////////////////////////////////////////
  //sprintf(gs,"beginning temp %6.1f",temp);
  //logit(1,gs);
  //
  //sprintf(gs,"ending    temp %6.1f",end_temp);
  //logit(1,gs);
  //
  //sprintf(gs,"nrep           %6d",nrep);
  //logit(1,gs);
  //
  //sprintf(gs,"reduction fact %6.4f",alpha);
  //logit(1,gs);
  //
  //sprintf(gs,"number of trials %8d",n_trials);
  //logit(1,gs);
  // DEBUG CODE ////////////////////////////////////////////////
  
  //=========================================================================
  // start simulated annealing process
  //=========================================================================

  do 
  {    

    for (rep=1;rep<=nrep;rep++)
    {
      try_nu_poly:;
	  //cand_poly= (((rand() << 15) + rand()) % NPOLY) + 1;
	  cand_poly= (rand() % NPOLY) + 1;
	
	  if ((cand_poly>NPOLY) || (cand_poly<1))
	  {
	    sprintf(gs,"poly number is out of range = %d",cand_poly);
	    logit(2,gs);
	  }
	  else
	  {
	    //printf("cand_poly = %d\n",cand_poly);
	  }
	
	  if (strcmp(own_type[cand_poly],ownership)!=0)
	  {
	    goto try_nu_poly;
	  }
	
	  st=strata_link[cand_poly];
	  // if (st==zero)
	  if (strcmp(st,zero) == 0)
	  {
	    goto try_nu_poly; // not a forest poly
	  }

      st_key = get_key_from_strata(st);
      if ( st_key == -1 )
      {
        goto try_nu_poly; // poly's strata did not appear in cut, live, or carbon data
      }
	
	  px=poly_biz_px[cand_poly];
	
	  if (px==0) goto try_nu_poly;
	  if (px >= 1 && px < NPX)
	  {
	    offset=rand() % NOFF;
	    //printf("Offset = %d\n",offset);
	  }
	
	  //=========================================================================
	  //check adjacency 
	  //=========================================================================
	
	
	  if (acres[cand_poly] < MIN_ACREAGE_FOR_ADJ_CHECK)
	  {
	    goto skip_adjcheck;
	  }
	
	  k1=beg_adj_ptr[cand_poly];
	  k2=end_adj_ptr[cand_poly];
	
	  for (k=k1;k<=k2;k++)
	  {
	    adj_poly=adj_list[k];   // adjacent poly
	    
	    if (strcmp(own_type[cand_poly],own_type[adj_poly])!=0)
	    {
		  goto nextk;
	    }	     
	    if (acres[adj_poly] < MIN_ACREAGE_FOR_ADJ_CHECK)
	    {
		  goto nextk;  // dont worry about slivers and rip polys
	    }
	    sta=strata_link[adj_poly];
	    // if (sta==zero)
	    if (strcmp(sta,zero) ==0)
	    {
		  goto nextk;
	    }
           
	    sta_key = get_key_from_strata(sta);
        if (sta_key == -1 )
        {
          goto nextk;
        }
	     
	    pxa=poly_biz_px[adj_poly];
	    offadj=soln[adj_poly];  // offset for adjacent poly
	     
	    for (tp=1;tp<=NTP;tp++)  // clearcut assumed to have 20 mbf/acre
	    {
		  if ((x_cutbfvol[st_key][px][offset][tp] > CLEARCUT_TEST_THRESHHOLD) &&  
		     (x_cutbfvol[sta_key][pxa][offadj][tp] > CLEARCUT_TEST_THRESHHOLD))
	      {
            goto try_nu_poly;
	      }
	    }
nextk:;
	  } // next k
	 
skip_adjcheck:;

      //=========================================================================
	  //check age restriction
	  //=========================================================================

      for (tp=1;tp<=NTP;tp++)
	  {
        if ( x_age[st_key][px][prev_offset[cand_poly][tp]][tp] == ADVANCED_AGE &&
                x_age[st_key][px][offset][tp] != ADVANCED_AGE )
        {
          if ( (advanced_acres[tp] - acres[cand_poly]) / total_acres < MIN_ADVANCED_PCT ) 
          {
            goto try_nu_poly;
          } 
        }
      }
	 
	  // DEBUG CODE ////////////////////////////////////////////////
	  // Print some debug...
	  //if (x_cutbfvol[st_key][px][offset][tp] != 0)
      //  {
	  //    sprintf(gs, "New offset - x_cutbfvol[%d][%d][%d][%d]=%d",st_key, px, offset, tp, x_cutbfvol[st_key][px][offset][tp]); logit(1,gs);
	  //  }
	  // DEBUG CODE ////////////////////////////////////////////////

	  //=========================================================================
	  // find value of temporary solution by adjusting current obj function value
	  //=========================================================================
	 
	  temp_obj=0.0;  
      temp_carbon=0.0;
	  poffset=soln[cand_poly];
	  for (tp=1; tp<=NTP; tp++)   //Changed start point from 0 because of weird data alignment (temp counts from zero, obj counts from 1) TODO
	  {	
	    // DEBUG CODE ////////////////////////////////////////////////
	    //if (x_cutbfvol_valid[st_key][px][offset][tp] != 1)
	    //  {
	    //	 temp_obj = 0.1;
	    //	 //sprintf(gs, "* Applying offset for invalid criteria - %d,%d,%d,%d",st_key,px,offset,tp); logit(1,gs);
	    //  }
	    change=((x_cutbfvol[st_key][px][offset][tp]*acres[cand_poly])-
	     (x_cutbfvol[st_key][px][poffset][tp]*acres[cand_poly]))/TO_MMBFPY_DENOM;   

	    //C_change=((x_C_tons[st_key][px][offset][tp]*acres[cand_poly])-
	    //     (x_C_tons[st_key][px][poffset][tp]*acres[cand_poly]));
      	     
	    temp_obj+=m1*pow(fabs(target_vol[tp]-(vol_per_period[tp]+change)),OBJ_EXPONENT);     
        temp_carbon+= carbon_per_period[tp];
	  } 	
      if (CARBON_WEIGHT != 0) {
        temp_obj = temp_obj/(CARBON_WEIGHT * temp_carbon);
      }
	 
	  //=============================================================
	  //  decide whether to accept candidate
	  //=============================================================
	 
	  delta=temp_obj - obj; 

	  if (delta<0)
	  {

	    //	     printf( "delta: %f, temp: %f, ex: %f, x: %f\n", delta, temp, ex, x );

	    // DEBUG CODE ////////////////////////////////////////////////
	    //sprintf(gs, "* Applying offset because objective function changed for the better"); logit(1,gs);
	    //sprintf(gs, "  - delta=%7.4f obj=%7.4f temp_obj=%7.4f cand_poly=%d poffset=%d",delta,obj,temp_obj,cand_poly,poffset);
	    //logit(1,gs);
	    // DEBUG CODE ////////////////////////////////////////////////

	    obj=temp_obj;
	    obj_it++;

	    soln[cand_poly]=offset;
	    soln_modified[cand_poly]++;

	    best_obj = obj;
	     
	    for (tp=1;tp<=NTP;tp++)
	    {
          vol_per_period[tp]+=(x_cutbfvol[st_key][px][offset][tp]*acres[cand_poly]-
				       x_cutbfvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM;  
          if (cubic_data == 0) 
          {
            cub_vol_per_period[tp]+=(x_cutcubvol[st_key][px][offset][tp]*acres[cand_poly]-
				       x_cutcubvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMCUBFPY_DENOM;
          }
                       
		  for ( spec=0;spec<NSPECIES;spec++ )
		  {
		    spec_vol_per_period[tp][spec] += (x_cutbfvol_spec[st_key][px][offset][tp][spec]*acres[cand_poly]-  
						       x_cutbfvol_spec[st_key][px][poffset][tp][spec]*acres[cand_poly])/TO_MMBFPY_DENOM;
            if (cubic_data == 0) 
            { 
              spec_cub_vol_per_period[tp][spec] += (x_cutcubvol_spec[st_key][px][offset][tp][spec]*acres[cand_poly]-  
						       x_cutcubvol_spec[st_key][px][poffset][tp][spec]*acres[cand_poly])/TO_MMBFPY_DENOM;
            }

		    if ( fabs(spec_vol_per_period[tp][spec]) > 0.001 && spec_vol_per_period[tp][spec] < 0 )
		    {
			  sprintf(gs,"negative species vol poly");
			  logit(2,gs);
		    }

		  }

		  carbon_per_period[tp]+=(x_C_tons[st_key][px][offset][tp]*acres[cand_poly]-
				       x_C_tons[st_key][px][poffset][tp]*acres[cand_poly]);

		  livevol_per_period[tp]+=(x_livevol[st_key][px][offset][tp]*acres[cand_poly]-
				       x_livevol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM_LIVE;

		  obj_per_period[tp] = m1*pow(fabs(target_vol[tp]-vol_per_period[tp]),OBJ_EXPONENT);

		  if ( fabs(vol_per_period[tp]) > 0.001 && vol_per_period[tp] < 0 )
		  {
		    sprintf(gs,"negative vol poly:%d rx:%d tp:%d (%f leaving %f)", cand_poly, px, tp,
			   (x_cutbfvol[st_key][px][offset][tp]*acres[cand_poly]-                                   
			    x_cutbfvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM,
			    vol_per_period[tp]);
		    logit(2,gs);
		  }
          
          if ( x_age[st_key][px][prev_offset[cand_poly][tp]][tp] == ADVANCED_AGE &&
                x_age[st_key][px][offset][tp] != ADVANCED_AGE )
          {
            advanced_acres[tp] -= acres[cand_poly];
          }
          
          if ( x_age[st_key][px][prev_offset[cand_poly][tp]][tp] != ADVANCED_AGE &&
                x_age[st_key][px][offset][tp] == ADVANCED_AGE )
          {
            advanced_acres[tp] += acres[cand_poly];
          }
          
          prev_offset[cand_poly][tp] = offset;
		     
	    } 
	  }
	  else
	  {	
	    // Make sure we do not get stuck at a local max, toss in another
	    // random jump to get unstuck.
	    
	    x=rand () % 1000;
	    x=x/1000.0;
	    ex=exp(-delta/temp);

	    if (x<ex)
	    {
		  // DEBUG CODE ////////////////////////////////////////////////
		  //sprintf(gs, "** Selecting a random poly offset to avoid local min/max");  logit(1,gs);
		  //sprintf(gs, "  - x=%7.4f ex=%7.4f cand_poly=%d poffset=%d",x,ex,cand_poly,poffset);
		  //logit(1,gs);
		  // DEBUG CODE ////////////////////////////////////////////////
		 
		  obj=temp_obj;
		  obj_it_rand++;

		  soln[cand_poly]=offset;
		  soln_modified[cand_poly]++;
		 
		  for (tp=1;tp<=NTP;tp++)
		  {
		    vol_per_period[tp]+=(x_cutbfvol[st_key][px][offset][tp]*acres[cand_poly]-          
					  x_cutbfvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM;
            if (cubic_data == 0) 
            { 
              cub_vol_per_period[tp]+=(x_cutcubvol[st_key][px][offset][tp]*acres[cand_poly]-    
					  x_cutcubvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMCUBFPY_DENOM;
            }

		    for ( spec=0;spec<NSPECIES;spec++ )
		    {
			  spec_vol_per_period[tp][spec] += (x_cutbfvol_spec[st_key][px][offset][tp][spec]*acres[cand_poly]-          
							   x_cutbfvol_spec[st_key][px][poffset][tp][spec]*acres[cand_poly])/TO_MMBFPY_DENOM;
              if (cubic_data == 0) 
              {
                spec_cub_vol_per_period[tp][spec] += (x_cutcubvol_spec[st_key][px][offset][tp][spec]*acres[cand_poly]-
							   x_cutcubvol_spec[st_key][px][poffset][tp][spec]*acres[cand_poly])/TO_MMCUBFPY_DENOM;
              }

			  if ( fabs(spec_vol_per_period[tp][spec]) > 0.001 && spec_vol_per_period[tp][spec] < 0 )
			  {
			    sprintf(gs,"negative species vol poly");
			    logit(2,gs);
			  }
		    }


		    carbon_per_period[tp]+=(x_C_tons[st_key][px][offset][tp]*acres[cand_poly]-
				       x_C_tons[st_key][px][poffset][tp]*acres[cand_poly]);

		    livevol_per_period[tp]+=(x_livevol[st_key][px][offset][tp]*acres[cand_poly]-
				       x_livevol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM_LIVE;

		    if ( fabs(vol_per_period[tp]) > 0.001 && vol_per_period[tp] < 0 )
		    {
			  sprintf(gs,"negative vol poly:%d rx:%d tp:%d (%f leaving %f)", cand_poly, px, tp,
				(x_cutbfvol[st_key][px][offset][tp]*acres[cand_poly]-
				 x_cutbfvol[st_key][px][poffset][tp]*acres[cand_poly])/TO_MMBFPY_DENOM,     
				vol_per_period[tp]);
			  logit(2,gs);
		    }

            if ( x_age[st_key][px][prev_offset[cand_poly][tp]][tp] == ADVANCED_AGE &&
                x_age[st_key][px][offset][tp] != ADVANCED_AGE )
            {
              advanced_acres[tp] -= acres[cand_poly];
            }
            
            if ( x_age[st_key][px][prev_offset[cand_poly][tp]][tp] != ADVANCED_AGE &&
                x_age[st_key][px][offset][tp] == ADVANCED_AGE )
            {
              advanced_acres[tp] += acres[cand_poly];
            }
            
            prev_offset[cand_poly][tp] = offset;

		  } 
	    }
	    else
	    {
		obj_no_change++;
	    }
	  }
	 
    } // next rep
     
    temp=alpha*temp;
    temp_change_it++;
  } while (temp>end_temp);
   
  sprintf(gs,"found better fit: %d;  randomized: %d;  no change: %d;  temp change loops: %d",
	  obj_it, obj_it_rand, obj_no_change, temp_change_it);
  logit(2,gs);

  //====================================================================
  // summary
  //===================================================================
   
   
  sprintf(gs, "----------------------------------------------");  logit(1,gs);
  sprintf(gs, "Ending Cut Volume Per Period - Offsets Applied::   ");  logit(1,gs);
  volume_total = 0.0;

  for (tp=0;tp<=NTP;tp++)
  {  
    //sprintf(gs, "tp %3d   vol %7.4f   target %5.1f   var %7.2f   func %7.2f   C %7.4f   live %7.4f",
    //	       tp, vol_per_period[tp], target_vol[tp], vol_per_period[tp]/target_vol[tp], obj_per_period[tp], carbon_per_period[tp], livevol_per_period[tp]);  
    sprintf(gs, "tp %3d   vol %7.4f   live %7.4f   C %7.4f  adv %5.3f%%",
	    tp, vol_per_period[tp], livevol_per_period[tp], carbon_per_period[tp], 100*advanced_acres[tp]/total_acres);
    logit(1,gs);       
    volume_total += vol_per_period[tp];
  }

  sprintf(gs, "----------------------------------------------");  logit(1,gs);
  sprintf(gs, "Total Volume for %s = %7.4f",ownership,volume_total);  logit(1,gs);
  sprintf(gs, "Final objective function for %s = %7.4f",ownership,obj);  logit(2,gs);
  sprintf(gs, "Best objective function seen for %s = %7.4f",ownership,best_obj);  logit(2,gs);
  sprintf(gs, "----------------------------------------------\n");  logit(1,gs);
   
  // Dump the solutions per poly
  if ((fin = fopen(out_file_txt, "w")) == NULL) 
  {
    fprintf(stderr, "Unable to open file %s\n",out_file_txt);
    exit(1);
  }
  for (i=1;i<=NPOLY;i++)
  {
    if (strcmp(own_type[i],ownership)==0)
	{
	  //fprintf(fin,"%d,%d,%d,%d\n",i,poly_biz_px[i],soln[i],soln_modified[i]);
	  fprintf(fin,"%d,%d,%d\n",i,poly_biz_px[i],soln[i]);
	}   
  }
  fclose(fin);


  // write out the summary info
  if ((fin = fopen(out_file_summary, "w")) == NULL) 
  {
    fprintf(stderr, "Unable to open file %s\n",out_file_summary);
    exit(1);
  }

  // per-species cuts: write a header
  fprintf( fin, "Per-species cuts by time period\n" );
  fprintf( fin, "tp\t" );
  for ( spec = 0; spec < species_count; spec++ )
  {
    fprintf( fin, species_map[spec] );
    fprintf( fin, "\t" );
  }
  fprintf( fin, "total\n" );
       
  // per-species cuts: write the data
  for ( tp = 0; tp <= NTP; tp++ )
  {
    fprintf( fin, "%d\t", tp);
    for ( spec = 0; spec < species_count; spec++ )
	{
	  fprintf( fin, "%f\t", fabs(spec_vol_per_period[tp][spec]) );     
	}
    fprintf( fin, "%f\n", vol_per_period[tp] );
  }
  fprintf( fin, "\n\n" );
   
  if (cubic_data == 0) 
  {
    // per-species cubic cuts: write a header
    fprintf( fin, "Per-species cuts by time period in cubic feet\n" );
    fprintf( fin, "tp\t" );
    for ( spec = 0; spec < species_count; spec++ )
    {
      fprintf( fin, species_map[spec] );
      fprintf( fin, "\t" );
    }
    fprintf( fin, "total\n" );
       
    // per-species cubic cuts: write the data
    for ( tp = 0; tp <= NTP; tp++ )
    {
      fprintf( fin, "%d\t", tp);
      for ( spec = 0; spec < species_count; spec++ )
      {
        fprintf( fin, "%f\t", fabs(spec_cub_vol_per_period[tp][spec]) );
      }
      fprintf( fin, "%f\n", cub_vol_per_period[tp] );
    }
    fprintf( fin, "\n\n" );
       
    // live, cut, cubic, carbon: write a header
    fprintf( fin, "Live, cut, cubic, carbon totals by time period\n" );
    fprintf( fin, "tp \tLive \tCut \tCubic \tCarbon \n" );
      
    // live, cut, cubic, carbon: write the data
    for ( tp = 0; tp <= NTP; tp++ )
    {
      fprintf( fin, "%d\t%f\t%f\t%f\t%f\n", tp, fabs(livevol_per_period[tp]), fabs(vol_per_period[tp]), fabs(cub_vol_per_period[tp]), fabs(carbon_per_period[tp]) ); 
    }
       
  }
  else
  {
    // live, cut, carbon: write a header
    fprintf( fin, "Live, cut, carbon totals by time period\n" );
    fprintf( fin, "tp \tLive \tCut \tCarbon \n" );
       
    // live, cut, carbon: write the data
    for ( tp = 0; tp <= NTP; tp++ )
    {
      fprintf( fin, "%d\t%f\t%f\t%f\n", tp, fabs(livevol_per_period[tp]), fabs(vol_per_period[tp]), fabs(carbon_per_period[tp]) ); 
    }
  }
  fclose(fin);

  // Why the fabs()? Floating point rounding errors can leave a 0 value as -0. 
   
} // end of harvest


/******************************************************************************\
 * Function:: main
 *
 * @argc - Number of arguments
 * @argv - Argument array
 * 
 * @int - 1=OK, 0=error
 *
\******************************************************************************/
int main (int argc, char *argv[])
{
  int result = 0;
  int return_code = 0;
  double target_vol = 0;
  double boost_percent = 0;
  int boost_periods = 0;
  int first_boost_period = 0;
  char owner_type[256];
  char alt_biz[256];
  int alt_biz_bin = 0;
  char in_file_pat[256];
  char in_file_cut[256];
  char in_file_cut_cu[256];
  char in_file_live[256];
  char in_file_carbon[256];
  char in_file_age[256];
  
  strata_link = (char (*)[MAX_STR_LENGTH]) malloc(sizeof(char) * (NPOLY+1) * MAX_STR_LENGTH);
  strata_map = (char (*)[MAX_STR_LENGTH]) malloc(sizeof(char) * (NSTRATA_MAP+1) * MAX_STR_LENGTH);

  if (argc != 7)
    {
      fprintf(stderr,"Usage : %s [alt|bus] owner_type target_vol %_boost #_boost_periods 1st_boost_period\n",argv[0]);
      fprintf(stderr," bus - ./data/bus_cut.txt and ./data/bus_pat.txt\n");
      fprintf(stderr," alt - ./data/alt_cut.txt and ./data/alt_pat.txt\n");
      exit(1);
    }

  sprintf(alt_biz,"%s",argv[1]);
  if (strcmp(alt_biz,"alt")==0)
    {
      sprintf(in_file_pat,"./data/alt_pat.txt");
      sprintf(in_file_cut,"./data/alt_cut_vol.txt");
      sprintf(in_file_cut_cu,"./data/alt_cut_vol_cu.txt");
      sprintf(in_file_live,"./data/alt_live.txt");
      sprintf(in_file_carbon,"./data/alt_car.txt");
      sprintf(in_file_age,"./data/alt_age.txt");
      alt_biz_bin = 1;
    }
  else if (strcmp(alt_biz,"bus")==0)
    {
      sprintf(in_file_pat,"./data/bus_pat.txt");
      sprintf(in_file_cut,"./data/bus_cut_vol.txt");
      sprintf(in_file_cut_cu,"./data/bus_cut_vol_cu.txt");
      sprintf(in_file_live,"./data/bus_live.txt");
      sprintf(in_file_carbon,"./data/bus_car.txt");
      sprintf(in_file_age,"./data/bus_age.txt");
      alt_biz_bin = 0;
    }
  else
    {
      fprintf(stderr,"Please select alt or bus...\n");
      exit(1);      
    }

  sprintf(owner_type,"%s",argv[2]);
  if (strcmp(owner_type,"PI")!=0 && strcmp(owner_type,"STATE")!=0 && strcmp(owner_type,"FED")!=0 && strcmp(owner_type,"PNI")!=0)
    {
      fprintf(stderr,"Owner type must be PI, STATE, FED, or PNI...\n");
      exit(1);
    }
  
  target_vol = (double)atof(argv[3]);
  boost_percent = (double)atof(argv[4]);
  boost_periods = atoi(argv[5]);
  first_boost_period = atoi(argv[6]);

  // start logging
  if ((log_fout = fopen("output.log", "a+")) == NULL) 
    {
      fprintf(stderr, "Unable to open file output.log\n");
      exit(1);
    }
  else
    {
      time_t rawtime;
      time( &rawtime );
      fprintf(log_fout, "\n\n %s -- Scheduler run %s %s %f %f %d %d\n\n", ctime(&rawtime), alt_biz, owner_type, target_vol, boost_percent, boost_periods, first_boost_period);
    }


  // Zero out the memory
  memset(own_type,0,sizeof(own_type));
  memset(x_cutbfvol,0,sizeof(x_cutbfvol));
  if (cubic_data == 0) 
  {
    memset(x_cutcubvol,0,sizeof(x_cutcubvol));
    memset(x_cutcubvol_spec,0,sizeof(x_cutcubvol_spec));
  }
  memset(acres,0,sizeof(acres));
  memset(strata_link,0,sizeof(strata_link));
  memset(strata_map,0,sizeof(strata_map));
  memset(poly_biz_px,0,sizeof(poly_biz_px));
  memset(beg_adj_ptr,0,sizeof(beg_adj_ptr));
  memset(end_adj_ptr,0,sizeof(end_adj_ptr));
  memset(adj_list,0,sizeof(adj_list));
  memset(x_cutbfvol_spec,0,sizeof(x_cutbfvol_spec));
  memset(species_map,0,sizeof(species_map));

  printf("Reading adj file\n");
  result = read_in_adj_file("./data/adj.txt");  
  if (result == 0)
    {
      printf("We had an error reading in the adj file (./data/adj.txt)... program aborted!\n");
      return_code = 0;
      exit(0);
    }
    
  printf("Reading pat file\n");
  result = read_in_pat_file(in_file_pat);  
  if (result == 0)
    {
      printf("We had an error reading in the poly attribute file (%s)... program aborted!\n",in_file_pat);
      return_code = 0;
      exit(0);
    }
    
  printf("Reading cut file\n");
  result = read_in_cut_file(in_file_cut);  
  if (result == 0)
    {
      printf("We had an error reading in the cut file (%s)... program aborted!\n",in_file_cut);
      return_code = 0;
      exit(0);
    }
    
  printf("Reading cut_cu file\n");
  read_in_cut_cu_file(in_file_cut_cu);
    
  printf("Reading live file\n");
  result = read_in_live_file(in_file_live);  
  if (result == 0)
    {
      printf("We had an error reading in the live file (%s)... \n",in_file_live);
    }
    
  printf("Reading car file\n");
  result = read_in_car_file(in_file_carbon);  
  if (result == 0)
    {
      printf("We had an error reading in the car file (%s)... \n",in_file_carbon);
    }
    
  printf("Reading age file\n");
  result = read_in_age_file(in_file_age);  
  if (result == 0)
    {
      printf("We had an error reading in the age file (%s)... \n",in_file_age);
    }
    
  // Lets process the data
  harvest(alt_biz_bin, owner_type, target_vol, boost_percent, boost_periods, first_boost_period);

  fclose(log_fout);

  return_code = 1;

  return return_code;
}
