#!/usr/bin/perl


if ( $ARGV[0] eq "" )
{
    print "\nUsage: cut_extract_sp_og.pl [bus|alt]\n";
    print " alt - run against data in ./alt_treelists\n";
    print " bus - run against data in ./bus_treelists\n\n";
    exit(1);
}

# read and eval the init file
if (open(INIT_FILE, "init.cfg"))
{
    while(<INIT_FILE>)
    {
	$init_file = $init_file.$_;
    }
    eval( $init_file );
    close(INIT_FILE);
}
else
{
    print "\nCould not open init.cfg -- please copy from a previous project and edit to appro. values.\n\n";
    exit(1);
}


$dir_root = $ARGV[0];
$data_dir = "./".$dir_root."_treelists";

$trl_cnt = 0;

open( LOG_FILE, ">>output.log" ) or die "Can't open log file: $!";
$nowstring = localtime;
print LOG_FILE "\n\n $nowstring -- running cut_extract_sp_of.pl $dir_root\n\n";

#If you want to run a system command...
#system("/home/mikem/bin/foo.pl $WORK_DIR");


#species specific variables
for ( my $i = 0; $i < $num_species_groups; $i++ )
{
    $species_vol_og[$i]=0;
    $species_vol_y[$i]=0;
}


opendir(NCDIR,$data_dir);
@lines = readdir(NCDIR);
close(NCDIR);

@lines = sort @lines;

%missing_species = ();

#Find all of the files in a dir
#Open an output file for the new search and replace
if (open(FILE_HAND_OUT_SP, ">$data_dir/".$dir_root."_cut_vol.txt"))
{
if (open(FILE_HAND_OUT, ">$data_dir/".$dir_root."_cut.txt"))
{
    
#Loop over each output tree list file and extract pertinent info.
    foreach $line (@lines)
    {
        #init some variables
	$total_cut = 0;
	$prev_rx = AF_1;
	$prev_plot = BareGrnd;
	$cur_period = 0;
	$prev_period = 0;
	$linesprocessed = 0;
	$cutlist = 0;
	$trl_count = 0;

	chomp($line);
	#print "File Name: $line \n";
	
	#If the file name indicates a tree list file
	if ($line =~ /\.trl/)
	    
	{
            #establish a counter to see how many files are parsed
            $trl_cnt = $trl_cnt + 1;
	    $fname = $line;
	    print "Processing $data_dir/$fname\n";
	    
	    #Open the individual file
	    if (open(FILE_HAND, "$data_dir/$fname"))
	    {
                #set the firstrun variable
		$firstrun = 1;
		#write the prescrip and offset here
		$prescrip_text = substr($fname,0,2);

		# look for this prescrip_text in the defs loaded from our init.cfg
		$prescrip = -1;
		for ( my $i = 1; $i < @prescrip_def; $i++)
		{
		    if ( $prescrip_text eq $prescrip_def[$i] )
		    {
			$prescrip = $i;
			last;
		    }
		}
		
		if ( $prescrip == -1 )
		{
		    print "\nWARNING: unknown prescription: ".$prescrip_text."\n\n";
		    print LOG_FILE "\nWARNING: unknown prescription: ".$prescrip_text."\n\n";
		    close( FILE_HAND );
		    next;
		}

    
				$offset = substr($fname,3,2);
               
            #when we use two characters, it pulls a . with single digit offsets
            #so we'll want to extract just the one digit.
                       if ($offset =~ /\./)
                            {
                              $offset = substr($fname,3,1);
                            }

	      #print "prescrip = $prescrip and offset = $offset\n";
	
		#Now lets loop through the lines and search and replace
		while (<FILE_HAND>)
		{
		    $tmp_line = $_;
		    #Strip the new line for printing to the screen
		    chomp($tmp_line);
		    #print "Just read in this line: $tmp_line \n";
		    #if the line contains header data lets not write it!
		    #otherwise we need to figure a way to extract a specific collumn
                    
                    if ($tmp_line =~ /FOREST/ or $tmp_line =~ /NUMBER/ or $tmp_line =~ /MORTAL/ or $tmp_line =~ /-----/ or $tmp_line eq "" or $tmp_line =~ /TREE LIST/) 
		    {
                        #if it's a tree list we need to reset cutlist to 0
                        #so we don't read tree data
			if ($tmp_line =~ /TREE LIST/)
			{
			    $cutlist = 0;
			}
			$proc_nextline = 0;  #what's this for?
			#print "this is just the header line \n";
		    }
		    else
		    {
                        #determine if it's the start of a cutlist 
                        #and set a variable that indicates to start proccessing 
                        #the next lines if it is
                        if ($tmp_line =~ /CUT/)
		        {
                            $cutlist = 1;
			    $proc_nextline = 1;
			    #extract the plot info
			    $cur_rx = substr($tmp_line,65,4);
			    $cur_plot = substr($tmp_line,29,8);
			    if ($cur_plot =~ /are/) 
			    {
				#print "plot = bare ground\n";
				$cur_plot = 1;
			    } 

			    $cur_year = substr($tmp_line,114,4);

                      #added one because for some reason it wasn't recording the appropriate year - this
                      #is problematic and needs to be diagnosed!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                      #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			    #$cur_period = int(($cur_year - $zero_year) / $period_length) + 1;
                      #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                      #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                      #perhaps a conditional statement that checks to see if the difference between
                      #zero year and cur_year is less than period length and if it is set it to period
                      #length so we don't get the wrong period
                      if (($period_one_year - $zero_year) lt ($period_length / 2))
			    {
			        $cur_period = int(($cur_year - $zero_year) / $period_length) + 1;
			    } 
                      else
			    {
                          $cur_period = int(($cur_year - $zero_year) / $period_length);
			    } 


			    #$cur_period = substr($tmp_line,82,2);  #we extract this to see if 
                                          #it's just a continuation of the same cut list or we've
                                          #moved to a new period.
                            #test to see if we moved to a new plot
                            #if so reset firstrun because we've been skipping the first line
                            #of each new plot
                            #lets print those to the screen
                            #print "plot = $cur_plot\n";
                            #print "period = $cur_period\n";
                            if ($cur_period ne $prev_period)  #means we've moved on to a new plot or period
			    {
				#write and reset everything
                                    #first adjust the plot and cutperiod
#				    if ($prev_period > 0)
#				    {
#					$cutperiod = $prev_period - 1; #for printing results
					#$cur_period = $prev_period - 1;
#				    }
#				    else
				    {
					$cutperiod = $prev_period;
					#$cur_period = $prev_period;
				    }  
                                    if ($prev_plot =~ /BareGrnd/)
				    {
					$cut_plot = 1;
				    }
				    else
				    {
					$cut_plot = substr($prev_plot,0,5);
					$cut_plot =~ s/\s+$//;
				    }
                                    #need to take one off of period for input into scheduler
                                    $o_field = $prescrip."_".$offset."_".$cut_plot;   
                                    #sometimes the total cut is 0 so we wont want to write it.
				    #print "plot = $cut_plot, volume = $total_cut \n";                                    
				    if ($total_cut > 0)
				    {      
					$o_field = $prescrip."_".$offset."_".$cut_plot;
					print  FILE_HAND_OUT $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$total_cut.",".$o_field."\n";
				    }
				    
                                    #also create the species specific table
                                    if ($total_cut > 0)
				    {     
					for ( my $i = 0; $i < $num_species_groups; $i++ )
					{
					    print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$spc_rprt_lbl[$i][0]." ,".$species_vol_og[$i].",".$o_field."\n";
					    print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$spc_rprt_lbl[$i][1]." ,".$species_vol_y[$i].",".$o_field."\n";
					}

					print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",total ,".$total_cut.",".$o_field."\n";
				    }

                                    #reset the variables
                                    $linesprocessed = 0;
				    $total_cut = 0;
				    $prev_rx = $cur_rx;
				    $prev_plot = $cur_plot;
				    $prev_period = $cur_period;  #this is being set when a line is not processed
                                                 #it's like it prints to the file only after it reads the first line in a new
                                                 #new cutlist - it should be doing it when it moves o a new period
                                                 #PRIOR to reading the next line - it's a matter of where the condition is set.

				    
                                    #species specific variables
				    for ( my $i = 0; $i < $num_species_groups; $i++ )
				    {
					$species_vol_og[$i]=0;
					$species_vol_y[$i]=0;
				    }
				}
			}                        
			#extract the tree info
			else  #see this is where it's already moved to the next line. We should write and
                              #reset everything while in the cut condition
			{
			    if ($cutlist == 1)
			    {
				#test to see if the cur_period is equal to the previous, 
				#if it's not we'll re-init the cut variable (set to 0)
                                #if it's the first run through on a new file, we need to
                                #set prev_period = cur_period (be sure to reset firstrun)
                                if ($firstrun == 1)
				{
				    $prev_period = $cur_period;
                                    $firstrun = 0;
				}
				if ($cur_period eq $prev_period) 
				{
				    #this is where we extract the bf and diameter and apply
				    #the 32 foot log function to get volume, we can then
				    #add it to the total volume
				    $cut = substr($tmp_line,110,7);  #MCH BD FT VOL
				    $dbh = substr($tmp_line,48,5); #CURR DIAM
				    $tpa = substr($tmp_line,30,8); #TREES PER ACRE
				    $volume = $cut*$tpa; #changed from the 32 foot conversion
				    
                                    #extract the species 
                                    $spec = substr($tmp_line,14,2); 
                                    #first print it to make sure we got it right
                                    
				    
				    #this is where we would tally the totals for different logs as well
				    #if df then
				    
				    if ($volume == 0)
				    {
					# ignore, do nothing
				    }
				    elsif ( exists $species_hash{$spec} )
				    {
					$spec_index = $species_hash{$spec};
					if ( $dbh > $species_og_vs_y_dbh[ $spec_index ] )
					{
					    $species_vol_og[ $spec_index ] = $species_vol_og[ $spec_index ] + $volume;
					}
					else
					{
					    $species_vol_y[ $spec_index ] = $species_vol_y[ $spec_index ] + $volume;
					}
				    }
				    elsif ( !exists $missing_species{$spec} )
				    {
					print "WARNING: cut unknown species: ".$spec."  (further incidents suppressed)\n";
					print LOG_FILE "WARNING: cut unknown species: ".$spec."  (further incidents suppressed)\n";
					$missing_species{$spec} = 0;
				    }
				    		    
				    
				    $total_cut = $volume + $total_cut;
				    $linesprocessed = $linesprocessed + 1;
				}
		
			    }
			}
			$proc_nextline = $proc_nextline + 1;
		    }#this ends the test for header condition (actually the else clause)!!!!!!!!!!!!!!
		    }#this ends the while loop, move to next line in file
		    close(FILE_HAND);
		#write the results from the last plot
		#first adjust the plot and cutperiod
#		if ($prev_period > 0)
#		{
#		    $cutperiod = $prev_period - 1;
#		}
#		else
#		{
		    $cutperiod = $prev_period;
#		}
		if ($prev_plot =~ /BareGrnd/)
		{
		    $cut_plot = 1;
		}
		else
		{
		    $cut_plot = substr($prev_plot,0,5);
		    $cut_plot =~ s/\s+$//;
		}       
                #need to take one off of period for input into scheduler
                $o_field = $prescrip."_".$offset."_".$cut_plot;	 
		if ($total_cut > 0)
		{      
			$o_field = $prescrip."_".$offset."_".$cut_plot;
			print  FILE_HAND_OUT $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$total_cut.",".$o_field."\n";

		}       

		if ($total_cut > 0)
		{     
		    for ( my $i = 0; $i < $num_species_groups; $i++ )
		    {
			print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$spc_rprt_lbl[$i][0]." ,".$species_vol_og[$i].",".$o_field."\n";
			print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",".$spc_rprt_lbl[$i][1]." ,".$species_vol_y[$i].",".$o_field."\n";
		    }
		    
		    print  FILE_HAND_OUT_SP $prescrip.",".$offset.",".$cut_plot.",".$cutperiod.",total ,".$total_cut.",".$o_field."\n";
		}

		#reset the variables
		$total_cut = 0;
		$prev_rx = $cur_rx;
		$prev_plot = $cur_plot;
		$prev_period = $cur_period;

		#species specific variables
		for ( my $i = 0; $i < $num_species_groups; $i++ )
		{
		    $species_vol_og[$i]=0;
		    $species_vol_y[$i]=0;
		}

	    }#if trl file opened
		else
	    {
		print "can't open file $data_dir/$fname \n";
		exit(1);
	    }	    
	}#if the file is a trl
	}#for each file 
    }#if output did not open
else
{
    print "Can't open file $data_dir/$fname.new \n";
    exit(1);
}  
}
close(FILE_HAND_OUT);
close(FILE_HAND_OUT_SP);

print "++++++++++++++++++++++++++++++++++++++\n";
print "+      Processed $trl_cnt files !!!!                 +\n";
print "++++++++++++++++++++++++++++++++++++++\n";

print LOG_FILE "Processed $trl_cnt files.\n";
close(LOG_FILE);


if (open(TEST_SCRIPT, "test.pl"))
{
    $cmd_string = "perl test.pl $data_dir ".$dir_root."_cut.txt ".$dir_root."_cut.test-ref";
    print `$cmd_string`;
    $cmd_string = "perl test.pl $data_dir ".$dir_root."_cut_vol.txt ".$dir_root."_cut_vol.test-ref";
    print `$cmd_string`;
    close(TEST_SCRIPT);
}
