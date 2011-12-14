#!/usr/bin/perl

#Created from gy_text_extract to generate a
#file with all standing volume / rx/ period/ offset

if ( $ARGV[0] eq "" )
{
    print "\nUsage: gy_live_extract.pl [bus|alt]\n";
    print " alt - run against data in ./alt_treefiles\n";
    print " bus - run against data in ./bus_treefiles\n\n";
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
print LOG_FILE "\n\n $nowstring -- running gy_live_extract.pl $dir_root\n\n";


#If you want to run a system command...
#system("/home/mikem/bin/foo.pl $WORK_DIR");


opendir(NCDIR,$data_dir);
@lines = readdir(NCDIR);
close(NCDIR);

@lines = sort @lines;

#Find all of the files in a dir
#Open an output file for the new search and replace
if (open(FILE_HAND_OUT, ">$data_dir/".$dir_root."_live.txt"))
{
    
    #Loop over each output tree list file and extract pertinent info.
    foreach $line (@lines)
    {
        #init some variables
	$total_cut = 0;
	$prev_rx = None;
	$prev_plot = BareGrnd;
	$cur_period = 0;
	$prev_period = 0;
	$linesprocessed = 0;
	$treelist = 0;


	chomp($line);
	#print "File Name: $line \n";
	
	#If the file name indicates a tree list file
	if ($line =~ /\.trl/)
	#if ($line =~ /AB_per5\.trl/)	
	{
            #establish a counter to see how many files are parsed
            $trl_cnt = $trl_cnt + 1;
	    $fname = $line;
	    print "Trying to open $data_dir/$fname\n";
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
                    
                    if ($tmp_line =~ /FOREST/ or $tmp_line =~ /NUMBER/ or $tmp_line =~ /MORTAL/ or $tmp_line =~ /-----/ or $tmp_line eq "" or $tmp_line =~ /CUT LIST/) 
		    {
                        #if it's a tree cutlist we need to reset treelist to 0
                        #so we don't read cut data
			if ($tmp_line =~ /CUT LIST/)
			{
			    $treelist = 0;
			}
			$proc_nextline = 0;
			#print "this is just the header line \n";
		    }
		    else
		    {
                        #determine if it's the start of a cutlist 
                        #and set a variable that indicates to start proccessing 
                        #the next lines if it is
                        if ($tmp_line =~ /TREE LIST/)
		        {
                            $treelist = 1;
			    $proc_nextline = 1;
			    #extract the plot info
			    $cur_rx = substr($tmp_line,65,4);
			    $cur_plot = substr($tmp_line,29,8);

                            #pull the period from the year instead of the cut cycle - 
                            #cut cycles are hugely problematic!
			    #$cur_period = substr($tmp_line,82,2);
			    $cur_year = substr($tmp_line,114,4);
                 
                      if ($cur_year == $zero_year)
                         {
                          #print "$cur_year\n";
                          $cur_period = 0
                         }
                      else
                         {
			       $cur_period = int(($cur_year - $period_one_year) / $period_length) + 1;
                         #print "$cur_period\n";
                         }
			    #test to see if we moved to a new plot
                            #if so reset firstrun because we've been skipping the first line
                            #of each new plot
            
			}                        
			#extract the plot info
			else
			{
			    if ($treelist == 1)
			    {
				#test to see if the cur_rx is equal to the previous, 
				#if it's not we'll re-init the cut variable (set to 0)
                                #if it's the first run through on a new file, we need to
                                #set prev_period = cur_period (be sure to reset firstrun)
                                if ($firstrun == 1)
				{
				    $prev_period = $cur_period;
                                    $firstrun = 0;
				}

				#Print the new text to the output file if we've moved on to another plot
				if ($cur_period ne $prev_period)
				{
                            #first adjust the plot and cutperiod
				    if ($prev_period > 0)
				    {
					$cutperiod = $prev_period - 1;
					
                                        #need to add one off of period for live tree lists
					$liveperiod = $cutperiod + 1;
				    }
				    else
				    {
					$cutperiod = $prev_period;
					$liveperiod = 0;
				    }  
                                    if ($prev_plot =~ /BareGrnd/)
				    {
					$cut_plot = 1;
				    }
				    else
				    {
					$cut_plot = substr($prev_plot,0,8);
					$cut_plot =~ s/\s+$//;
				    }
                                    #also create an o_field for feeding into sum_offsets model!
				    $o_field = $prescrip."_".$offset."_".$cut_plot;
				    print  FILE_HAND_OUT $prescrip.",".$offset.",".$cut_plot.",".$liveperiod.",".$total_cut.",".$o_field."\n";
				    #reset the variables
                                    $linesprocessed = 0;
				    $total_cut = 0;
				    $prev_rx = $cur_rx;
				    $prev_plot = $cur_plot;
				    $prev_period = $cur_period;
				}

				#this is where we extract the bf and diameter and apply
				#the 32 foot log function to get volume, we can then
				#add it to the total volume
				$cut = substr($tmp_line,110,7);
				$dbh = substr($tmp_line,48,5);
				$tpa = substr($tmp_line,30,8);
				$volume = $cut*$tpa;
				$total_cut = $volume + $total_cut;
                                $linesprocessed = $linesprocessed + 1;
			    }
			}
			$proc_nextline = $proc_nextline + 1;
		    }#this ends the test for header condition (actually the else clause)!!!!!!!!!!!!!!
		    }#this ends the while loop, move to next line in file
		    close(FILE_HAND);
		#write the results from the last plot
		#first adjust the plot and cutperiod
		if ($prev_period > 0)
		{
		    $cutperiod = $prev_period - 1;
		}
		else
		{
		    $cutperiod = $prev_period;
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
                
		#need to add one off of period for live tree lists
		$liveperiod = $cutperiod + 1;
                #also create an o_field for feeding into sum_offsets model!
                $o_field = $prescrip."_".$offset."_".$cut_plot;
		print  FILE_HAND_OUT $prescrip.",".$offset.",".$cut_plot.",".$liveperiod.",".$total_cut.",".$o_field."\n";
		#reset the variables
		$total_cut = 0;
		$prev_rx = $cur_rx;
		$prev_plot = $cur_plot;
		$prev_period = $cur_period;
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
close(FILE_HAND_OUT);

print "++++++++++++++++++++++++++++++++++++++\n";
print "+      Processed $trl_cnt files !!!!                 +\n";
print "++++++++++++++++++++++++++++++++++++++\n";

print LOG_FILE "Processed $trl_cnt files.\n";
close(LOG_FILE);



if (open(TEST_SCRIPT, "test.pl"))
{
    $cmd_string = "perl test.pl $data_dir ".$dir_root."_live.txt ".$dir_root."_live.test-ref";
    print `$cmd_string`;
    close(TEST_SCRIPT);
}
