"""Provides a scripting component.
    This is a script running inside a custom node in a visual scripting language
    called Grasshopper
    
    Inputs:
        Path: filepath to path.csv
        Tracker: filepath to tracker.csv
        Tol: duplicate point tolerance
        
    Outputs are visualized in Rhino-Grasshopper
"""

__author__ = "jake newsum"
__version__ = "2022.02.26"

import rhinoscriptsyntax as rs
import csv

class PathPoint():
    """ 
    get Index, Point, and T params from CSV
    Not sure what T param is for at this time
    """
    Point = None
    Index = None
    T = None
    
    def __init__(self, index, point, t):
        self.Index = index
        self.Point = point
        self.T = t

class PathPlanChecker():
    """
    PathPlan will be used to evaluate PathPoints
    """
    def __init__(self, pathPoints):
        
        self.PathPoints = pathPoints
        self.BadPathPoints = []
        self.BadPathPointCounts = []
    
    def RemoveDuplicatePoints(self, tol = 1.0):
        """ look for sequential duplicate points within tol"""
        uniquePathPoints = []
        uniquePathIndices = []
        searchPoint = None
        mostDuplicatesRemoved = 0
        numSequentialDuplicates = 0
        for p, pathPoint in enumerate(self.PathPoints):
            if p == 0:
                #get start point to begin
                uniquePathPoints.append(pathPoint)
                uniquePathIndices.append(p)
                searchPoint = pathPoint.Point
                continue
            #check if point is withing tol of searchPoint
            dist = rs.Distance(searchPoint, pathPoint.Point)
            if (dist > tol):
                uniquePathPoints.append(pathPoint)
                uniquePathIndices.append(p)
                searchPoint = pathPoint.Point
                if numSequentialDuplicates > 0:
                    self.BadPathPoints.append(pathPoint) #keep track of bad points
                    self.BadPathPointCounts.append(numSequentialDuplicates) #store count for visual
                if numSequentialDuplicates > mostDuplicatesRemoved:
                    mostDuplicatesRemoved = numSequentialDuplicates #get most
                numSequentialDuplicates = 0 #always reset counter
            else:
                numSequentialDuplicates+=1
        print "Removed: ", len(uniquePathIndices)
        print "Most Sequential Removed: ", mostDuplicatesRemoved
        return uniquePathPoints

def ReadPathPointsCSV (csvPath):
    pathPoints = []
    
    with open(csvPath, 'rb') as csvFile:
        dialect = csv.Sniffer().sniff(csvFile.read(1024))
        csvReader = csv.reader(csvFile, dialect)
        
        for l, line in enumerate(csvReader):
            #if l > 10000: break # run fast when debugging
            
            if l == 0:
                #skip header
                continue
            index = int(line[1])
            point = rs.AddPoint(float(line[2]), float(line[3]), float(line[4]))
            t = float(line[5])
            pathPoint = PathPoint(index, point, t)
            pathPoints.append(pathPoint)
            
    return pathPoints

def WritePathPointsCSV(pathPoints, csvPath):
    
    return true

def main(path, tracker, tol):
    """
    Thoughts:
        Need read the csv files into points
        Need to figure out the transfrom from path to tracker
        Need to inspect path and tracker points to find issues:
            robot failed to follow path
            "does its best" to go to points in order
            'just sat there unmoving" 
        Why would a robot fail to move for a moment along a path?:
            Could be the motion parameters - velocity, acceleration, approximation...
            Could be point distribution - can't read points fast enough
            Could be network issue if streaming:
            Could be workspace or safety issue - 
                robots slow to almost 0 mm/s when close to Workspace boundary
        What can I check with the data?:
            See if there is the tool stops in similare areas
            See if there are issues in path.csv in the areas tracker.csv at the same location
            find transform between points
    """
    
    
    # Read point in from path.csv to inspect input to robot
    pathPoints = ReadPathPointsCSV(path)
    # check to see if pathPoints have bad data
    pathChecker = PathPlanChecker(pathPoints)
    cleanPathPathPoints = pathChecker.RemoveDuplicatePoints(tol)
    # output cleanPoints for visualization in grasshopper
    cleanPathPoints = [pPoint.Point for pPoint in cleanPathPathPoints]
    pathBadPathPoints = pathChecker.BadPathPoints
    # output badPoints and counts for visualization in grasshopper
    pathBadPoints = [pPoint.Point for pPoint in pathBadPathPoints]
    pathBadPointCounts = pathChecker.BadPathPointCounts
    # write clean csv - try running this on the robot to see if it resolves the issues
    
    #WritePathPointsCSV(cleanPathPathPoints) - TODO
    
    """ looks like there were sequential duplicate points
    This could cause the robot to have trouble moving in a smooth path
    if the APO.CIS is set larget than tol (1.0), then the robot would have
    trouble interpolating through these points.
    There would also be issues if the robot is moving faster than the
    controller can process the points. This is especially problematic when 
    streaming points using UDP/TCP protocols. 
    In this case, many of the points  are 0.0mm appart, so the robot is being
    told to move to the same location which is why it appears to stop.
    
    Inspection - with Tol set to 0.01mm 40 pathPoints had duplicates.
    The first point had 96 duplicates and the others had 119.
    See image - DuplicatePathCounts.png
    Try running the cleanPath.csv to see if this fixes this issue.
    """
    
    """
    Check tracker.csv:
        Need to find transform to overlay points
        See how fast tool was moving by point distribution
        Check to see where the tool stopped
        Make sure it matches areas where path had duplicate points
    """
    trackerPoints = ReadPathPointsCSV(tracker)
    trackerChecker = PathPlanChecker(trackerPoints)
    cleanTrackerPathPoints = trackerChecker.RemoveDuplicatePoints(tol)
    cleanTrackerPoints = [pPoint.Point for pPoint in cleanTrackerPathPoints]
    trackerBadPathPoints = trackerChecker.BadPathPoints
    trackerBadPoints = [pPoint.Point for pPoint in trackerBadPathPoints]
    trackerBadPointCounts = trackerChecker.BadPathPointCounts
    
    """
    After comparing duplicate points of path and tracker,
    it seems the duplicate points did coorelate with the concentrations of points
    in tracker.csv. (see images)
    """
    
    """
    To find the transform and aling paths, I used Grasshopper. It is much
    easier to write and visualize the code with their native tools. 
    I always use the appropriate tools for the job, and this is a great example.
    
    I found the centered average plane for each path and tracker
    To do this I found the average of all points to be the origin
    I found the 2 farthest points away from each other to be X vector
    I then found the normal of the average plane from all points
    This gave me a great approximate plane for both collections
    You can see t he point overlays with errors in images.
    """
    
    tPoints = None
    return pathBadPoints, pathBadPointCounts, cleanPathPoints, trackerBadPoints, trackerBadPointCounts, cleanTrackerPoints


if __name__ == "__main__":
    PathBadPoints, PathBadPointCounts, CleanPathPoints, TrackerBadPoints, TrackerBadPointCounts, CleanTrackerPoints = main(Path, Tracker, Tol)
