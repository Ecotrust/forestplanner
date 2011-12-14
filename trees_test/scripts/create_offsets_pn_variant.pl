#!/usr/bin/perl

#used to create offsets from all prescrips in a given
#directory (keyfiles dir)
#outputs will be stored in a seperate (offsets) directory?
#this directory will be destroyed and re-created each time

#If you want to pass arguments...
#$WORK_DIR = $ARGV[0];
#$data_dir = "..\\FVS\\BaseRX";
$data_dir = $ARGV[0];
$offsets_dir = $ARGV[1];



opendir(NCDIR,$data_dir);
#get a list of all files (should only be base key files)
@lines = readdir(NCDIR);
close(NCDIR);

#Find all of the files in a dir
#Open an output file for the new search and replace\
#we'll want to loop through 4 times for each file
#and create 4 offsets (2-5).  Copy these as well as the
#base to the offsets directory


    
#Loop over each file.
foreach $line (@lines)
{
    if ($line =~ /.key/)
    {
	print("We have a File: $line\n");
	#extract the rx
	$fname = $line;
	$rx = substr($fname,0,2);
	
	$i = 1;

#changed this to 9 offsets
	while ($i<10)
#	while ($i<6)
	{
	    
	    #copy the file to a new file with appropriate offset
	    system("copy $data_dir/$line $offsets_dir/$rx/_$i.key");
	    
	    #init the hit counter
	    $edit_nextline = 0;
	    
	    if (open(FILE_HAND, "$data_dir/$line"))
	    {
		#open the file and begin editing	    
		if (open(FILE_HAND_OUT, ">$offsets_dir/$rx/_$i.key"))
		{
		    #establish a variable to track offset calc
		    $o_calc = ($i - 1) * 5;
#changed this to 1998 - 2004 for sooes
                    $year_calc = ($o_calc + 2010);
		    #next loop through the entire file line by line
		    while (<FILE_HAND>)
		    {		
			#now perform the edits in the file (find and replaces)
			s/$rx\_1/$rx\_$i/;
			
			#find the appropriate occurence of offset (after compute $start year)
                        #need to know what the start year is for this to work!!!!!!!!
                        #this line triggers whether to edit the next line so if
                        #we hit it we want to set a variable to adjust the following line
			if ($_ =~ /Compute/ && $_ =~ /2010/)
			{
			    $edit_nextline = 1;
			}
			elsif ($edit_nextline == 1)
			{
			    s/0/$o_calc/;
			    $edit_nextline = 0;
			}
                        #now print it to the new file   
			print FILE_HAND_OUT $_;
			#end the loop through the file
		    }
		    close(FILE_HAND_OUT);
		}
		else
		{
		    print "Can't open file $offsets_dir/$rx/_$i.key\n";
		    exit(1);
		}
		close(FILE_HAND);

		#still within the offset loop we want to create a
                #bat file that will be used to execute fvs from tycho (php script)
                #these files will be stored in the same location (offsets dir)
                #and have imbeded names that reflect that of the key files

                #what about the bat for the no-offset scenario?
               
                #open the file
		if (open(BAT_HAND_OUT, ">$offsets_dir/$rx/_$i.bat"))
		    {
#begin bat file==================================
			print BAT_HAND_OUT "rem StdFVS run on DOS\n";
			print BAT_HAND_OUT "echo $rx\_$i.key >  $rx\_$i.rsp\n";
			print BAT_HAND_OUT "echo $rx\_$i.tre >> $rx\_$i.rsp\n";
			print BAT_HAND_OUT "echo $rx\_$i.out >> $rx\_$i.rsp\n";
			print BAT_HAND_OUT "echo $rx\_$i.trl >> $rx\_$i.rsp\n";
			print BAT_HAND_OUT "echo $rx\_$i.sum >> $rx\_$i.rsp\n";
			print BAT_HAND_OUT "echo $rx\_$i.chp >> $rx\_$i.rsp\n";
			print BAT_HAND_OUT "if not exist $rx\_$i mkdir $rx\_$i\n";
			print BAT_HAND_OUT "C:\\Fvsbin\\FVSpn.exe < $rx\_$i.rsp\n";
			print BAT_HAND_OUT "if not exist $rx\_$i\_index.svs rmdir $rx\_$i\n";
			print BAT_HAND_OUT "del $rx\_$i.rsp\n";
			print BAT_HAND_OUT "\@echo off\n";
			print BAT_HAND_OUT "C:\\Fvsbin\\grep.exe -n FVS...ERROR $rx\_$i.out > $rx\_$i.err\n";
			print BAT_HAND_OUT "C:\\Fvsbin\\grep.exe -n FVS...WARNING $rx\_$i.out >> $rx\_$i.err\n";
			print BAT_HAND_OUT "\@echo on\n";
#end file=========================================
			close(BAT_HAND_OUT);
		    }
#need to unix2dos the bat files
#try to make adjustment for go files (no offsets required)
		if ($rx =~ /GO/ and $i > 1)
		{
		    system("del $offsets_dir/$rx/_$i.bat");
		    system("del $offsets_dir/$rx/_$i.key");
		}
		else
		{
                if ($i == 9)
                    {
		          system("del $offsets_dir/$rx/_$i.bat");
		          system("del $offsets_dir/$rx/_$i.key");
                      system("copy $offsets_dir/GO/_1.bat $offsets\\$rx\_$i.bat");
                      system("copy $offsets_dir/GO/_1.key offsets\\$rx\_$i.key");
                    }

		    #system("unix2dos offsets\\$rx\_$i.bat offsets.\$rx\_$i.bat");
		}               
	    }
	    else
	    {
		print "Can't open file $data_dir\\$line\n";
		exit(1);
	    }   
	    #move to next offset
	    $i++;
	}
	#move to the next file
    }
}

