#!/usr/bin/perl

#Created from gy_text_extract to generate a
#file with all carbon by rx/ period/ offset

if ( $ARGV[0] eq "" )
{
    print "\nUsage: gy_carbon_extract.pl [bus|alt]\n";
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
print LOG_FILE "\n\n $nowstring -- running gy_carbon_extract.pl $dir_root\n\n";


#init some variables
$total_cut = 0;
$prev_rx = AF_1;
$prev_plot = BareGrnd;
$prev_period = 0;
$linesprocessed = 0;
$trl_count = 0;
$first_space = 1;
$print_totals = 0;
$firstrun = 1;
$getready = 0;
$getset = 0;
$line_count = 0;


opendir(NCDIR,$data_dir);
@lines = readdir(NCDIR);
close(NCDIR);

@lines = sort @lines;

#Open an output file for the new search and replace
if (open(FILE_HAND_OUT, ">$data_dir/".$dir_root."_car.txt"))
{
    
#Loop over each file in directory.
    foreach $line (@lines)
    {
	chomp($line);
	#print "File Name: $line \n";
	
	#If the file name indicates a tree list file
	if ($line =~ /\.out/)	
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

		
		#Now lets loop through the lines and search and replace
		while (<FILE_HAND>)
		{
		    $tmp_line = $_;
		    #Strip the new line for printing to the screen
		    chomp($tmp_line);
		    #print "Just read in this line: $tmp_line \n";
		    #if the line contains header data lets not write it!
		    #otherwise we need to figure a way to extract a specific collumn
		    #check to see if it's a tree list
		    
                #check to see if we get to stand data
                if ($tmp_line =~ /STAND CARBON REPORT/)
                {
                   $getready = 1;
                }
                if ($tmp_line =~ /STAND ID/ && $getready == 1)
		    {
			    $treelist = 1;
			    #extract the plot info
			    $cur_rx = $prescrip;
			    $cur_plot = substr($tmp_line,10,8);
                      #print "$cur_plot\n";
                 }
                 if ($tmp_line =~ /YEAR/ && $getready == 1)
                 {
			    $getset = 1;
                 }
		     

#==========================================================
#================data proc
#=========================================================

                    if ($proc_nextline == 1)
                    {
			    #should do this 20 times so let's set up a counter
                      #after the 20th time we'll reset procenextline and
                      #print to the file
                      #print "$line_count\n";

                   
		
                            #print "processing data\n";
                            #check to see if it's the right data
                            $year = substr($tmp_line,0,4);
                            
				    #this is where we extract the carbon and 
                            #convert to co2e / acre
			
                            #car carbon pools include above ground live, below ground live
                            #standing dead and wood products (which is in a different table)

                            $agl = substr($tmp_line,8,5);
                            $bgl = substr($tmp_line,26,5);
                            $dead = substr($tmp_line,44,5);

				    $carbon = $agl + $bgl + $dead;
                            #rint "period $line_count year $year\n";

				    $co2_acre = (0.404685*$carbon)*3.66667;
                            $cur_period = $line_count;

				    if ($cur_plot =~ /Bare/)
				    {
				    $cur_plot = 1;
				    }
			          $o_field = $prescrip."_".$offset."_".$cur_plot;
                 	          print  FILE_HAND_OUT $prescrip.",".$offset.",".$cur_plot.",".$cur_period.",".$co2_acre.",".$o_field."\n";

                            $line_count = $line_count + 1;
                 #change this line if you want a different nber of periods!!!!
                            if ($line_count == $number_periods)
                            {
                            $proc_nextline = 0;
                            $line_count = 0;
                            $getready = 0;
                            $getset = 0;
                            } #end printing



	                  } #ends procing the line data


#just because it moves to another

#==========================================================
#================ end data proc
#=========================================================

                if ($tmp_line =~ /---/ && $getset == 1)
	             {
			      $proc_nextline = 1;
                        #print "$cur_plot\n";
                        $getready = 0;
                        $getset = 0;
                     }
			


		    }#this ends the while loop, move to next line in file
		    close(FILE_HAND);
		    }# ends if trl file opened
			else
		    {
			print "can't open file $data_dir/$fname \n";
			exit(1);
		    }	    
	}# ends if the file is a trl
	}# ends for each file in offsets dir
    }# ends if output did not open
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
    $cmd_string = "perl test.pl $data_dir ".$dir_root."_car.txt ".$dir_root."_car.test-ref";
    print `$cmd_string`;
    close(TEST_SCRIPT);
}





