#!c:\php\php.exe
<?php

print "----------------------------------------------\n";
echo " Starting to process FVS data from offsets directory \n";
echo "----------------------------------------------\n\n\n";
set_time_limit(0);

//script developed for extracting gy data from a sql database and
//formatting for input into the scheduling model.
//
//Required extraction includes:
//      building a query that joins data from multiple tables
//      
//
//Required formatting includes:
//      re-naming or assigning codes to prescriptions (1-5)??
//      re-naming of BareGrnd to 1
//Output file should be a compilation of all prescriptions for one scenario representing
//cutlist in the following format: prescription_id,offset,plot_id,period,cut
//all fields must have data!!!!
//plot_id of 1 = Baregrnd
//
//
//MODIFIED to execute fvs growth and yield on prescrip at a time. 
//remove the tables after each iteration, this will write data to the db
//much faster!



function calcElapsedTime($time)
{
  // calculate elapsed time (in seconds!)
  $diff = time()-$time;
  $yearsDiff = floor($diff/60/60/24/365);
  $diff -= $yearsDiff*60*60*24*365;
  $monthsDiff = floor($diff/60/60/24/30);
  $diff -= $monthsDiff*60*60*24*30;
  $weeksDiff = floor($diff/60/60/24/7);
  $diff -= $weeksDiff*60*60*24*7;
  $daysDiff = floor($diff/60/60/24);
  $diff -= $daysDiff*60*60*24;
  $hrsDiff = floor($diff/60/60);
  $diff -= $hrsDiff*60*60;
  $minsDiff = floor($diff/60);
  $diff -= $minsDiff*60;
  $secsDiff = $diff;
  return (''.$yearsDiff.' year'.(($yearsDiff <> 1) ? "s" : "").', '.$monthsDiff.' month'.(($monthsDiff <> 1) ? "s" : "").
	  ', '.$weeksDiff.' week'.(($weeksDiff <> 1) ? "s" : "").', '.$daysDiff.' day'.(($daysDiff <> 1) ? "s" : "").
	  ', '.$hrsDiff.' hour'.(($hrsDiff <> 1) ? "s" : "").', '.$minsDiff.' minute'.(($minsDiff <> 1) ? "s" : "").
	  ', '.$secsDiff.' second'.(($secsDiff <> 1) ? "s" : "").'');
}

// Mark the start time to try and make sure we keep track of how long all of this takes
$start_time = time();

// Welcome message
echo "----------------------------------------------\n";
echo " Starting to process FVS data from Postgresql \n";
echo "----------------------------------------------\n\n\n";

flush();


//make sure to save this php in the p47_r28\offsets dir!!!!!!!!!!!!!!!!!!!!!!
//re-write this loop to conduct in dir with key files.

if ($dirhandle = opendir('G:\Trees\projects\projects2011\bbi_elliot\analysis\scheduling\offsets')) 
{
   echo "Directory handle: $dirhandle\n";
   echo "Files:\n";
  //loop over each file and do something
  while (false != ($line = readdir($dirhandle))) 
    {
    print "File Name: $line \n";
    //If the file name indicates a bat file
    //extract the extension (leaves us with .*)
    $fname = strstr($line,'.');
    //get rid of the .
    //$fname=substr_replace($fname,'',0,1);  
      if ($fname == '.bat')
       {
	    
          //call the bat file (run fvs)
          $command = "call $line";
          echo $command."\n";
          exec($command);    
          //echo "got here\n";
        }
     }

fclose($dirhandle);

}

// Closing message
echo "----------------------------------------------\n";
echo " all done\n";
echo "----------------------------------------------\n\n\n";

$duration = calcElapsedTime($start_time);
printf("Online: ".$duration."\n");

?>