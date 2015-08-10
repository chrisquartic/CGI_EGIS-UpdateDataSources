#-------------------------------------------------------------------------------------------
# UpdateDataSources
# Purpose: Update paths in all map documents residing under a specified folder/directory.
# ArcGIS Version 10.1
# Python Version 2.7
# Created on: 04/02/2013
# Created by: Matthew McSpadden
# Edits:
#   McSpadden 03142014: Modified script so that original mxd is saved as mxd_BACKUP and new mxd is saved as mxd.

#-------------------------------------------------------------------------------------------
# Import system modules
import arcpy, os, sys, datetime
from datetime import datetime
startTime = datetime.now().strftime("%m%d%Y_%H%M%S")

# ------------------------------------------------------------------------------------------
# Local variables:
# txt report output
reportPath = sys.path[0]
infoFile = reportPath + "\\UpdateDataSources_" + startTime + ".txt"

#-------------------------------------------------------------------------------------------
# Read the parameter values:
# 0: Directory
#    Valid Values: System File or Directory
# 1: Old Workspace Path
#    Valid Values: String
# 2: Old Workspace Type
#    Valid Values: ACCESS_WORKSPACE, ARCINFO_WORKSPACE, CAD_WORKSPACE, EXCEL_WORKSPACE, FILEGDB_WORKSPACE,
#                  NONE, OLEDB_WORKSPACE, PCCOVERAGE_WORKSPACE, RASTER_WORKSPACE, SDE_WORKSPACE,
#                  SHAPEFILE_WORKSPACE, TEXT_WORKSPACE, TIN_WORKSPACE, VPF_WORKSPACE
# 3: New Workspace Path
#    Valid Values: Workspace
# 4: New Workspace Type
#    Valid Values: ACCESS_WORKSPACE, ARCINFO_WORKSPACE, CAD_WORKSPACE, EXCEL_WORKSPACE, FILEGDB_WORKSPACE,
#                  OLEDB_WORKSPACE, PCCOVERAGE_WORKSPACE, RASTER_WORKSPACE, SDE_WORKSPACE, SHAPEFILE_WORKSPACE,
#                  TEXT_WORKSPACE, TIN_WORKSPACE, VPF_WORKSPACE
# 5: Name Change Table
#    Valid format: Table must have an "Old_Name" and "New_Name" field. The fields must be text fields.
#
directory = arcpy.GetParameterAsText(0)
oldPath = arcpy.GetParameterAsText(1)
oldType = arcpy.GetParameterAsText(2)
newPath = arcpy.GetParameterAsText(3)
newType = arcpy.GetParameterAsText(4)
nameTbl = arcpy.GetParameterAsText(5)
#directory = 'C:\Users\mmcspadden'
#oldPath = 'ALL'
#oldType = 'NONE'
#newPath = 'Database Connections\city@atlasdev.sde'
#newType = 'SDE_WORKSPACE'
#nameTbl = newPath + '\\' + 'SDW.CITY.LAYERS_UPDATE_TABLE'
#fldOldTableName = 'SANGIS_LAYER_NAME'
#fldNewTableName = 'CITY_LAYER_NAME'


# ------------------------------------------------------------------------------------------
# Create output info text file.
tInfoFile = file(infoFile, 'wt')
tInfoFile = open(infoFile, 'w')
tInfoFile.write("Start Time: " + startTime)
tInfoFile.write("\n" + "\n")

# Report the process starting
tInfoFile.write("Parameters: " + "\n" + "Directory = " + directory + "\n" + "Old Workspace Path = "
                + oldPath + "\n" + "Old Workspace Type = " + oldType + "\n" + "New Workspace Path = "
                + newPath + "\n" + "New Workspace Type = " + newType)
if nameTbl <> "":
        tInfoFile.write("\n" + "Name Change Table = " + nameTbl)
tInfoFile.write("\n" + "\n")
tInfoFile.write("Finding Map Documents...")
tInfoFile.write("\n")

#-------------------------------------------------------------------------------------------
# Walk the directory tree starting at directory.
# Return the path, a list of directories, and a list of files.
# Find the mxds from the list of files and their full path
# Get access to the mxd.
try:
        for root, dirs, files in os.walk(directory):
                for filename in files:
                        extension = os.path.splitext(filename)
                        if extension[1] == ".mxd":
                            fullpath = os.path.join(root, filename)
                            mxd = arcpy.mapping.MapDocument(fullpath)
                            tInfoFile.write("Found " + fullpath + "\n")

                            # Save a backup of the mxd and report it.
                            copyPath = extension[0] + "_BACKUP" + extension[1]
                            mxd.saveACopy(copyPath)
                            tInfoFile.write("Saved Backup As: " + os.path.join(root, copyPath))
                            tInfoFile.write("\n")

                            # Attempt to fix paths in the mxd using replaceWorkspaces method.
                            try:
                                    tInfoFile.write("Attempting to replace workspaces..." + "\n")
                                    if oldPath == "ALL" and oldType == "NONE":
                                        mxd.replaceWorkspaces("", "NONE", newPath, newType)
                                        tInfoFile.write("Replace workspaces succeeded" + "\n")
                                    elif oldPath == "ALL" and oldType != "NONE":
                                        mxd.replaceWorkspaces("", oldType, newPath, newType)
                                        tInfoFile.write("Replace workspaces succeeded" + "\n")
                                    else:
                                        mxd.replaceWorkspaces(oldPath, oldType, newPath, newType)
                                        tInfoFile.write("Replace workspaces succeeded" + "\n")
                            except:
                                    tInfoFile.write("Failed to replace workspaces." + "\n")

                            # Get a list of layers in the mxd.
                            # Check if any layer names exist in the table specifying name changes(if supplied).
                            # If name is is the table, use the replaceDataSource method to fix path.
                            # Update the layers name in the mxd using the name attribute.
                            lyrList = arcpy.mapping.ListLayers(mxd)
                            try:
                                    if nameTbl != "":
                                        #nameTbl = newPath + '\\' + nameTbl
                                        tInfoFile.write("Checking for name changes..." + "\n")
                                        #with arcpy.da.SearchCursor(nameTbl, ["Old_Name", "New_Name"]) as cursor:
                                        #with arcpy.da.SearchCursor(nameTbl, ["SANGIS_LAYER_NAME", "CITY_LAYER_NAME"]) as cursor:
                                        with arcpy.da.SearchCursor(nameTbl, ["SANGIS_LAYER_NAME", "CITY_LAYER_NAME"]) as cursor:
                                                for row in cursor:
                                                        for lyr in lyrList:
                                                                if lyr.supports("datasetName"):
                                                                        dataset_name = lyr.datasetName
                                                                        lyrNameList = dataset_name.split(".")
                                                                        layerName = lyrNameList[-1]
                                                                        try:
                                                                                if row[0] == layerName:
                                                                                        newName = row[1]
                                                                                        lyr.replaceDataSource(newPath, newType, newName)
                                                                                        lyr.name = newName
                                                                        except:
                                                                                pass
                                                                                tInfoFile.write("Failed name change check for " + layerName + "\n")
                            except:
                                    pass
                                    tInfoFile.write("Failure during name change check." + "\n")
                            tInfoFile.write("Completed name change check" + "\n")

                            # Update each layers definition query and label SQL query(if not a table).
                            tInfoFile.write("Updating definition queries..." + "\n")
                            for lyr in lyrList:
                                        try:
                                                if newType == "FILEGDB_WORKSPACE" or newType == "SDE_WORKSPACE":
                                                        try:
                                                                if lyr.dataSource:
                                                                        lyr.definitionQuery = lyr.definitionQuery.replace("[", "\"")
                                                                        lyr.definitionQuery = lyr.definitionQuery.replace("]", "\"")
                                                                        lyr.definitionQuery = lyr.definitionQuery.replace("*", "%")
                                                        except:
                                                                pass # Layer doesn't support dataSource attribute.

                                                        try:
                                                                if lyr.supports("LABELCLASSES"):
                                                                        for lblClass in lyr.labelClasses:
                                                                                lblClass.SQLQuery = lblClass.SQLQuery.replace("[", "\"")
                                                                                lblClass.SQLQuery = lblClass.SQLQuery.replace("]", "\"")
                                                                                lblClass.SQLQuery = lblClass.SQLQuery.replace("*", "%")
                                                        except:
                                                                pass # Layer doesn't support labelClasses attribute.
                                        except:
                                                pass
                                                tIfnoFile.write("Failed while updating definition queries." + "\n")
                            tInfoFile.write("Updated definition queries" + "\n")

                            # Save the mxd and report it.
                            mxd.save()
                            tInfoFile.write("Saved MXD")
                            tInfoFile.write("\n")

# ------------------------------------------------------------------------------------------
# Write the output to the report.
        stopTime = datetime.now().strftime("%m%d%Y_%H%M%S")
        tInfoFile.write("Finished: " + stopTime)
        tInfoFile.write("\n")
        if tInfoFile:
                tInfoFile.close()

except Exception as e:
        tInfoFile.write("Major Error. Script Did Not Complete")
        tInfoFile.write(e.message)
finally:
        # make sure to close up the filinput no matter what.
        if tInfoFile:
                tInfoFile.close()







