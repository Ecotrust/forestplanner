import sys, os, csv

class StandProcessor(object):
            
    def create_stand_files(self, csv_file, input_slf_filename, outdir="."):
        
        print 'StandProcessor 1.2 (implements damage & severity codes)'
        print 'Working...'
        
        output_slf_filename = "stands.slf"
        
        # iterate over each entry in the list of stands we need to process
        exported_stands_list = open(input_slf_filename,'r')
        new_slf = open(os.path.join(outdir, output_slf_filename),'w')

        # add a bareground stand as the first stand in the list
        new_slf.write( 'A BareGrnd @ 0 pn @\n' )
        new_slf.write( 'B BareGrnd @\n' )

        # set default vals
        first_line = True
        
        # all the fields we may have for an SLF file
        pos_StandID = 0 
        pos_InvYr = -1
        pos_Lat = -1
        pos_Lon = -1
        pos_LocCode = -1
        pos_HabType = -1
        pos_OrigYr = -1
        pos_Aspect = -1
        pos_Slope = -1
        pos_Elev = -1
        pos_BasalAf = -1
        pos_InvLtFap = -1
        pos_InvStFap = -1
        pos_BkptDbh = -1
        pos_NumPlots = -1
        pos_Nonstock = -1
        pos_SampWt = -1
        pos_PropStockSa = -1
        pos_Dgtc = -1
        pos_DiaPer = -1
        pos_Hgtc = -1
        pos_HtPer = -1
        pos_MortPer = -1
        pos_BasArea = -1
        pos_MaxSdi = -1
        pos_IndSpec = -1
        pos_SiteIndex = -1
        pos_SubMod = -1
        pos_PhysioRc = -1
        pos_ForTc = -1
        pos_FiaSc = -1
        #pos_FiaCc = -1             # these weren't present in the reference output data set
        #pos_PotVegRc = -1      # these weren't present in the reference output data set
        
        # process the data rows
        for line in exported_stands_list:
            # chew the \n off the end of our last field
            if line[len(line)-1] == '\n':
                line = line[0:len(line)-1]
                
            slf_fields = line.split(',') # try splitting by comma first...
            if len(slf_fields) < 2:
                slf_fields = line.split('\t') # ... then try tab if that didn't work
            
            # check for and parse any header row
            if first_line:
                first_line = False
                
                if slf_fields[0] == 'StandID': # guess we have to require StandID be first to make this check
                
                    for i in range(len(slf_fields)):
                        if slf_fields[i] == 'StandID':
                            pos_StandID = i
                        elif slf_fields[i] == 'InvYr':
                            pos_InvYr = i
                        elif slf_fields[i] == 'OrigYr':
                            pos_OrigYr = i
                        elif slf_fields[i] == 'SiteIndex':
                            pos_SiteIndex = i
                        elif slf_fields[i] == 'NumPlots':
                            pos_NumPlots = i
                        elif slf_fields[i] == 'Lat':
                            pos_Lat = i
                        elif slf_fields[i] == 'Lon':
                            pos_Lon = i
                        elif slf_fields[i] == 'LocCode':
                            pos_LocCode = i
                        elif slf_fields[i] == 'HabType':
                            pos_HabType = i
                        elif slf_fields[i] == 'Aspect':
                            pos_Aspect = i    
                        elif slf_fields[i] == 'Slope':
                            pos_Slope = i
                        elif slf_fields[i] == 'Elev':
                            pos_Elev = i
                        elif slf_fields[i] == 'BasalAf':
                            pos_BasalAf = i
                        elif slf_fields[i] == 'InvLtFap':
                            pos_InvLtFap = i
                        elif slf_fields[i] == 'InvStFap':
                            pos_InvStFap = i
                        elif slf_fields[i] == 'BkptDbh':
                            pos_BkptDbh = i
                        elif slf_fields[i] == 'Nonstock':
                            pos_Nonstock = i
                        elif slf_fields[i] == 'SampWt':
                            pos_SampWt = i
                        elif slf_fields[i] == 'PropStockSa':
                            pos_PropStockSa = i
                        elif slf_fields[i] == 'Dgtc':
                            pos_Dgtc = i
                        elif slf_fields[i] == 'DiaPer':
                            pos_DiaPer = i
                        elif slf_fields[i] == 'Hgtc':
                            pos_Hgtc = i
                        elif slf_fields[i] == 'HtPer':
                            pos_HtPer = i
                        elif slf_fields[i] == 'MortPer':
                            pos_MortPer = i
                        elif slf_fields[i] == 'BasArea':
                            pos_BasArea = i
                        elif slf_fields[i] == 'MaxSdi':
                            pos_MaxSdi = i
                        elif slf_fields[i] == 'IndSpec':
                            pos_IndSpec = i
                        elif slf_fields[i] == 'SubMod':
                            pos_SubMod = i
                        elif slf_fields[i] == 'PhysioRc':
                            pos_PhysioRc = i
                        elif slf_fields[i] == 'ForTc':
                            pos_ForTc = i
                        elif slf_fields[i] == 'FiaSc':
                            pos_FiaSc = i
                        
                else: # no header row -- assume defaults
                    print '\nNo column names found in '+ pre_slf_filename
                    print 'Assuming defaults in order: '
                    print 'Stand ID, Inventory Year, Originating Year, Site Index, Num Plots\n'
                    
                    pos_StandID = 0
                    pos_InvYr = 1
                    pos_OrigYr = 2
                    pos_SiteIndex = 3
                    pos_NumPlots = 4
                
            if slf_fields[pos_StandID] == 'StandID': # skip the header row if it exists
                continue
            
            # make sure any -1 indexes map to the FVS default val character
            slf_fields.append('@')
            stand = slf_fields[pos_StandID]
            
            # this one screwy field can be populated from two different source columns
            if pos_BasalAf == -1:
                multi_field = slf_fields[pos_InvLtFap]
            else:
                multi_field = slf_fields[pos_BasalAf]
            
            # create the new .slf entries for this stand
            new_slf.write( 'A ' + stand + ' ' + stand + '.fvs NoPointData PN @\n' )
            new_slf.write( 'B ' + stand + ' ' + slf_fields[pos_InvYr] + ' ' + slf_fields[pos_Lat] + ' ' 
                + slf_fields[pos_Lon] + ' ' + slf_fields[pos_LocCode] +' '+ slf_fields[pos_HabType] + ' ' 
                + slf_fields[pos_OrigYr] + ' ' + slf_fields[pos_Aspect] + ' ' + slf_fields[pos_Slope] + ' ' 
                + slf_fields[pos_Elev] + ' ' + multi_field + ' '
                + slf_fields[pos_InvStFap] + ' ' + slf_fields[pos_BkptDbh] + ' ' + slf_fields[pos_NumPlots] + ' '
                + slf_fields[pos_Nonstock] + ' ' + slf_fields[pos_SampWt] + ' ' + slf_fields[pos_PropStockSa] + ' '
                + slf_fields[pos_Dgtc] + ' ' + slf_fields[pos_DiaPer] + ' ' + slf_fields[pos_Hgtc] + ' '
                + slf_fields[pos_HtPer] + ' ' + slf_fields[pos_MortPer] + ' ' + slf_fields[pos_BasArea] + ' '
                + slf_fields[pos_MaxSdi] + ' ' + slf_fields[pos_IndSpec] + ' ' + slf_fields[pos_SiteIndex] + ' '
                + slf_fields[pos_SubMod] + ' ' + slf_fields[pos_PhysioRc] + ' ' + slf_fields[pos_ForTc] + ' '
                + slf_fields[pos_FiaSc] + '\n' )
                
            # create a new output file for this stand
            output = open(os.path.join(outdir, stand + '.fvs'),'w')
            
            # now iterate over our exported database rows and add the trees that belong to the current stand
            input = open( csv_file, 'r' )
            
            for row in input:
                fields = row.split(',') # try splitting by comma first...
                if len(fields) < 2:
                    fields = row.split('\t') # ... then try tab if that didn't work
                    
                if fields[0] == 'Stand_ID': # skip the header row, if it exists
                    continue
                    
                stand_id = fields[0] # Stand_ID
                
                if type(stand_id) == int:
                    stand_id = float(stand_id)
                if type(stand) == int:
                    stand = float(stand)
                if (stand_id == stand):
                                    
                    output.write("%4u" % (int(float(fields[1])))) # ITRE - plot ID: col 1-4
                    
                    # our tree ID's are sometimes > 3 digits, so we're throwing away the leading digits if so
                    tree_id = fields[2]
                    if len(tree_id) > 3:
                        tree_id = tree_id[len(tree_id)-3:len(tree_id)] 
                        
                    output.write("%3u" % (int(float(tree_id)))) # IDTREE - tree ID: col 5-7
                    if float(fields[3]) < 1: # tricky logic here for fixed-width output: tree count gets 6 digits
                        tree_count_str = "%6.4g" % (float(fields[3])) # Force 6 total len: '0.' = 2, 4 left to use
                    else: 
                        tree_count_str = "%6.5g" % (float(fields[3])) # 5 digits and a '.' for all cases < 10,000
                        #this handles all cases from 0.0001 to 99,999.444 after that it's e notation
                    output.write(tree_count_str) # PROB - tree count: col 8-13
                    output.write("%1u" % (int(float(fields[4])))) # ITH - tree history: col 14
                    output.write("%-3s" % (fields[5])) # ISP - species: col 15-17
                    output.write("%4.1f" % (float(fields[6]))) # DBH - diameter at breast height: col 18-21
                    output.write("   ") # DG - DBH increment: col 22-24
                    
                    if fields[7] == '' or fields[7] == '\n':
                        output.write("   ")
                    else:
                        output.write("%3u" % (int(float(fields[7])))) # HT - live height: col 25-27
                        
                    output.write("   ") # THT - height to topkill: col 28-30
                    output.write("    ") # HTG - height increment: col 31-34
                    
                    # our ICR's are 2-3 digits, we only keep the first digit
                    if fields[8] == '' or fields[8] == '\n':
                        output.write(" ")
                    else:                    
                        icr = fields[8]
                        if icr[0:3] == '100': # special case test for icr value = 100
                            icr = '9'
                        else: # otherwise just take the tens digit
                            icr = icr[0:1]
                        output.write("%1d" % (int(float(icr)))) # ICR - crown ratio code: col 35
                    
                    # if we have additional fields, they are damage and severity codes
                    if len(fields) > 9:
                        output.write("%2d" % (int(float(fields[9])))) # IDCD - damage code: col 36-37
                        output.write("%2d" % (int(float(fields[10])))) # IDCD - severity code: col 38-39
                    else:
                        output.write("  ") # IDCD - damage code: col 36-37
                        output.write("  ") # IDCD - severity code: col 38-39
                        
                    output.write("  ") # IDCD - damage code: col 40-41
                    output.write("  ") # IDCD - severity code: col 42-43
                    output.write("  ") # IDCD - damage code: col 44-45
                    output.write("  ") # IDCD - severity code: col 46-47
                    output.write(" ") # IMC - tree value class: col 48
                    output.write("0") # IPRSC - cut or leave: col 49
                    
                    output.write('\n') # EOL
                
            output.close()
            
        new_slf.close()
        
        print '...Done.'
# end of Stand Processor class definition

# 
#sp = StandProcessor()
#
#if len(sys.argv) == 3:
#    sp.create_stand_files(sys.argv[1], sys.argv[2])
#elif len(sys.argv) == 4:
#    sp.create_stand_files(sys.argv[1], sys.argv[2], sys.argv[3])
#else: 
#    print ''
#    print 'You must provide the filename of the exported TreeList_forFVS query.'
#    print ''
#    print 'The file can be either comma or tab delimited, but fields must be in the order:'
#    print 'Stand_ID, Plot_ID, Tree_ID, Tree_Count, Tree_History, Species, DBH, HT, ICR, IDCD_dam, IDCD_sev (IDCD columns optional)'
#    print ''
#    treelist_file = 'Treelist_Elliott_VEGLBL.txt'
#    #raw_input("Enter the name of the exported TreeList_forFVS query: ")
#    pre_slf_file = 'SlfTbl_Elliott_VEGLBL.txt'
#    #raw_input("Enter the name of the file containing the data to make an SLF file: ")
#    print ''
#    sp.create_stand_files(treelist_file, pre_slf_file)

