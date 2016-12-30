import sys
import datetime
import random
from enum import Enum

# constants
DEFAULT_RUNNING_TIME=5
BEST_NUM_FLIGHTS = 3
MIN_TMP_SL = 20
MIN_TMP_TRC_TRIP = datetime.timedelta(minutes=30)
MAX_PS_TRIP = 5
LIM_POU_TRIP = 4
MAX_TMP_VOO_TRIP = 570  #9*60+30
LIM_TMP_VOO_TRIP = 1
MAX_ININT_TRIP = 720  #12*60
LIM_WRK_TRIP = 2
GROUP_FLAGS_MASK = 7  # LIM_WRK_TRIP|LIM_TMP_VOO_TRIP|LIM_POU_TRIP


class IATA(Enum):
    CGR = 1
    CGH = 2
    FOR = 3
    REC = 4
    CPQ = 5
    SDU = 6
    POA = 7
    CWB = 8
    VIX = 9
    PLU = 10
    MGF = 11
    BSB = 12
    GIG = 13
    FLN = 14
    SSA = 15
    GYN = 16
    NVT = 17


class Fleet:
    def __init__(self):
        self.tracklist = []

    def __str__(self):
        for track in self.tracklist:
            track.__str__()
            print("")
        print("Best solution used " + str(self.tracklist.__len__()) + " airplanes")


class Track:
    def __init__(self):
        self.landingPsgr = 0
        self.crewlanding = 0
        self.crewtotalflighttime = 0  # <9h30
        self.uninterruptedcrewflighttime = 0  # <12h
        self.flightlist = []

    def __str__(self):
        for flight in self.flightlist:
            flight.__str__()
        print("Number of flights registered for this track: " + str(self.flightlist.__len__()))


class Flight:
    def __init__(self, fc=0, seg=0, siata=0, diata=0, dture=0, arr=0, dlay=datetime.timedelta(0)):
        self.flightcode = fc
        self.segment = seg
        self.sourceiata = siata
        self.destinationiata = diata
        self.departure = datetime.datetime.strptime(dture, "%H:%M")
        self.arrival = datetime.datetime.strptime(arr, "%H:%M")
        self.delay = dlay
        self.repositioningdeparture = None
        self.repositioningarrival = None

    def __str__(self):
        print(self.flightcode + " " + self.segment + " " + self.sourceiata + " " +
              self.destinationiata + " " + self.departure.strftime("%H:%M:%S") + " " +
              self.arrival.strftime("%H:%M:%S") + " " + str(self.delay))


class PCTA:
    def __init__(self):
        self.filename = ""
        self.mesh = []
        self.iatamatrix = None
        self.fleet = None
        # comparison functions for selecting best candidates to algorithm
        self.comparisonfunc1 = lambda x: x.departure
        self.comparisonfunc2 = lambda x: x.delay
        self.comparisonfunc3 = lambda x: x.arrival
        # time of best solution found
        self.besttime = None
        # private
        self.__earlier__ = None
        self.__runningtime__ = datetime.timedelta(minutes=DEFAULT_RUNNING_TIME)

    def __str__(self):
        self.fleet.__str__()
        print("Best solution was found in time: " + str(self.besttime))

    def run(self):
        self.readfile()
        self.allociatamatrix()
        self.filliatamatrix()
        backupmesh = self.mesh.copy()
        tstart = datetime.datetime.now()
        while (datetime.datetime.now() - tstart) < self.__runningtime__:
            fleet = self.algorithm()
            if self.fleet is None:
                self.fleet = fleet
                self.besttime = datetime.datetime.now() - tstart
            elif fleet.tracklist.__len__() < self.fleet.tracklist.__len__():
                self.fleet = fleet
                self.besttime = datetime.datetime.now() - tstart
            # self.mesh is destroyed every iteration. Copy is necessary to avoid reference modification
            self.mesh = backupmesh.copy()

    def setrunningtime(self, dtime=5):
        self.__runningtime__ = datetime.timedelta(minutes=dtime)

    @staticmethod
    def iata2code(iata):
        if iata == 'CGR':
            return IATA.CGR.value
        if iata == 'CGH':
            return IATA.CGH.value
        if iata == 'FOR':
            return IATA.FOR.value
        if iata == 'REC':
            return IATA.REC.value
        if iata == 'CPQ':
            return IATA.CPQ.value
        if iata == 'SDU':
            return IATA.SDU.value
        if iata == 'POA':
            return IATA.POA.value
        if iata == 'CWB':
            return IATA.CWB.value
        if iata == 'VIX':
            return IATA.VIX.value
        if iata == 'PLU':
            return IATA.PLU.value
        if iata == 'MGF':
            return IATA.MGF.value
        if iata == 'BSB':
            return IATA.BSB.value
        if iata == 'GIG':
            return IATA.GIG.value
        if iata == 'FLN':
            return IATA.FLN.value
        if iata == 'SSA':
            return IATA.SSA.value
        if iata == 'GYN':
            return IATA.GYN.value
        if iata == 'NVT':
            return IATA.NVT.value


    # read from file the flight schedule
    def readfile(self):
        if self.filename == "":
            print("filename is not assigned")

        file = open(self.filename, 'r')
        lines = file.readlines()
        # line format: line number, flight code, track, iata1, iata2, departure, arrival
        for line in lines:
            args = line.split(" ")
            self.mesh.append(Flight(args[1], args[2], args[3], args[4], args[5], args[6].replace("\n", "")))
        file.close()

    def allociatamatrix(self):
        order = self.mesh.__len__() + 1
        self.iatamatrix = [[datetime.timedelta() for i in range(order)] for j in range(order)]

    # read file to fill iata matrix
    # the road time between airports that are not defined in the file must be treated separately
    # by default, there road time will be 0 (assumption that make not sense)
    def filliatamatrix(self):
        for segment in self.mesh:
            traveltime = segment.arrival - segment.departure
            siata = self.iata2code(segment.sourceiata)
            diata = self.iata2code(segment.destinationiata)
            self.iatamatrix[siata][diata] = traveltime
            self.iatamatrix[diata][siata] = traveltime

    @staticmethod
    def comparison1(flight1, flight2):
        if flight1.departure >= flight2.departure:
            return 1
        else:
            return 0

    @staticmethod
    def comparison2(flight1, flight2):
        if flight1.delay >= flight2.delay:
            return 1
        else:
            return 0

    @staticmethod
    def comparison3(flight1, flight2):
        if flight1.repositioningArrival >= flight2.repositioningArrival:
            return 1
        else:
            return 0

    def redefinegroundtimespecialcases(self, flight):
        if flight.sourceiata == IATA.PLU.value or flight.sourceiata == IATA.CPQ.value:
            return datetime.timedelta(minutes=15)
        elif flight.sourceiata == IATA.BSB.value or flight.sourceiata == IATA.CGH.value:
            return datetime.timedelta(minutes=25)
        else:
            return datetime.timedelta(minutes=20)

    @staticmethod
    def selectflightconstraint0():
        return True

    # CONSTRAINT: returns True whether fight2 departure time allows crew team changing (based on flags) or
    # at least a ground time
    def selectflightconstraint1(self, flight1, flight2, flags):
        if flight2.sourceiata == flight1.destinationiata:
            groundtime = self.redefinegroundtimespecialcases(flight2)

            if flags & LIM_TMP_VOO_TRIP or flags & LIM_WRK_TRIP or flags & LIM_POU_TRIP:
                return flight2.departure >= (flight1.arrival + MIN_TMP_TRC_TRIP) and \
                        flight2.sourceiata == flight1.destinationiata
            else:
                return flight2.departure >= (flight1.arrival + groundtime) and \
                        flight2.sourceiata == flight1.destinationiata

    # CONSTRAINT: returns True whether is possible to connect flight2 with flight1 using repositioning and/or delay
    def selectflightconstraint2(self, flight1, flight2, flags):
        if flight2.sourceiata == flight1.destinationiata and flight2.departure >= flight1.arrival:
            f1arrival = datetime.timedelta(hours=flight1.arrival.hour, minutes=flight1.arrival.minute, seconds=flight1.arrival.second)
            f2arrival = datetime.timedelta(hours=flight2.arrival.hour, minutes=flight2.arrival.minute, seconds=flight2.arrival.second)
            f2departure = datetime.timedelta(hours=flight2.departure.hour, minutes=flight2.departure.minute, seconds=flight2.departure.second)
            if flags & LIM_TMP_VOO_TRIP or flags & LIM_WRK_TRIP or flags & LIM_POU_TRIP:
                if (f2arrival + f2departure - f1arrival + MIN_TMP_TRC_TRIP) > datetime.timedelta(days=1):
                    return False
                flight2.delay = MIN_TMP_TRC_TRIP - (flight2.departure - flight1.arrival)
            else:
                groundtime = self.redefinegroundtimespecialcases(flight2)
                if (f2arrival + f2departure - f1arrival + groundtime) > datetime.timedelta(days=1):
                    return False
                flight2.delay = groundtime - (flight2.departure - flight1.arrival)

            if flight2.delay > groundtime or flight2.delay < datetime.timedelta(0):
                flight2.delay = datetime.timedelta(0)
                return False

            flight2.departure += flight2.delay
            flight2.arrival += flight2.delay
            return True
        return False

    # CONSTRAINT: returns True whether flight2 departure time is after the flight1 arrival time including
    # two ground times (before flight1 departure and after flight1 landing for flight connecting)
    def selectflightconstraint3(self, flight1, flight2, *args):
        groundtime = datetime.timedelta(minutes=2*MIN_TMP_SL)
        flightdistancetime = self.iatamatrix[self.iata2code(flight1.destinationiata)][self.iata2code(flight2.sourceiata)]
        mindeparturetime = flight1.arrival + groundtime + flightdistancetime
        if flight2.departure >= mindeparturetime:
            flight2.repositioningarrival = mindeparturetime
            return True
        return False

    # selects a flight from meshlist and returns it as the chose leg
    # This method removes the flight from meshlist
    @staticmethod
    def graspselectflight(meshlist):
        if meshlist.__len__() > BEST_NUM_FLIGHTS:
            selectedflight = random.randint(0, BEST_NUM_FLIGHTS - 1)
        else:
            selectedflight = random.randint(0, meshlist.__len__() - 1)
        return meshlist.pop(selectedflight)

    # adds a flight inside mesh verifying whether flights has delay.
    # if so, decrements delay from departure and arrival time
    def addflightmesh(self, flight):
        if flight.delay:
            flight.departure -= flight.delay
            flight.arrive -= flight.delay
            flight.delay = False
        self.mesh.append(flight)

    # performs no check in flight delay before append it to self.mesh
    def addflightmeshwithoutdelay(self, flight):
        self.mesh.append(flight)

    # sorts by arrival time
    def earlierdeparture(self, comparison):
        self.mesh.sort(key=comparison)

    # FIXME: explain what choosegroup means
    @staticmethod
    def choosegroup():
        choice = random.randint(0, 100)
        if choice < 90:
            return LIM_TMP_VOO_TRIP
        elif choice < 99:
            return LIM_WRK_TRIP
        else:
            return LIM_POU_TRIP

    @staticmethod
    def crewconstraints(track):
        flags = 0
        if track.crewlanding >= MAX_PS_TRIP:
            flags |= LIM_POU_TRIP
        if track.crewlanding >= MAX_TMP_VOO_TRIP:
            flags |= LIM_TMP_VOO_TRIP
        if track.crewlanding >= MAX_ININT_TRIP:
            flags |= LIM_WRK_TRIP
        return flags

    # def createlistofavailableflights(self, currentflight, flags, comparisonfunction):
    def createlistofavailableflights(self, currentflight, comparisonfunction, selectfunction, *args):
        flightschecked = 0
        flightstobechecked = self.mesh.__len__()
        meshidx = 0
        selectedflights = []

        while flightschecked < flightstobechecked:
            # if self.selectflightconstraint3(currentflight, self.mesh[meshidx]):
            if selectfunction(currentflight, self.mesh[meshidx], args[0]):
                selectedflights.append(self.mesh.pop(meshidx))
                meshidx -= 1
            meshidx += 1
            flightschecked += 1

        selectedflights.sort(key=comparisonfunction)
        return selectedflights

    def algorithm(self):
        fleet = Fleet()
        while self.mesh.__len__() > 0:
            # step 1: selects a new track head
            self.earlierdeparture(self.comparisonfunc3)
            flight = self.graspselectflight(self.mesh)

            # step2: selects flights that will make part of the track
            track = Track()
            track.flightlist.append(flight)

            restriction = 0
            while restriction != GROUP_FLAGS_MASK:
                while True:
                    group = self.choosegroup()
                    if not (group & restriction):
                        break
                # flags holds active constraints
                flags = self.crewconstraints(track)
                if group == LIM_TMP_VOO_TRIP:
                    flightlist = self.createlistofavailableflights(flight, self.comparisonfunc1,
                                                                   self.selectflightconstraint1, flags)
                    if flightlist.__len__() == 0:
                        restriction |= LIM_TMP_VOO_TRIP
                        choseflight = None
                    else:
                        choseflight = self.graspselectflight(flightlist)
                        # returns the nonselected flights to self.mesh
                        self.mesh.extend(flightlist)
                        restriction = 0
                elif group == LIM_WRK_TRIP:
                    flightlist = self.createlistofavailableflights(flight, self.comparisonfunc2,
                                                                   self.selectflightconstraint2, flags)
                    if flightlist.__len__() == 0:
                        restriction |= LIM_WRK_TRIP
                        choseflight = None
                    else:
                        choseflight = self.graspselectflight(flightlist)
                        # returns the nonselected flights to self.mesh
                        self.mesh.extend(flightlist)
                        restriction = 0
                elif group == LIM_POU_TRIP:
                    flightlist = self.createlistofavailableflights(flight, self.comparisonfunc3,
                                                                   self.selectflightconstraint3, flags)
                    if flightlist.__len__() == 0:
                        restriction |= LIM_POU_TRIP
                        choseflight = None
                    else:
                        choseflight = self.graspselectflight(flightlist)
                        # returns the nonselected flights to self.mesh
                        self.mesh.extend(flightlist)
                        restriction = 0
                else:
                    raise Exception("Undefined state")

                if choseflight is not None:
                    track.flightlist.append(choseflight)
                    flight = choseflight

            # builds the fleet
            fleet.tracklist.append(track)
        return fleet


def main(argv=sys.argv):
    if argv.__len__() < 2:
        print("Missing input filename parameter")
        sys.exit(-1)

    pcta = PCTA()
    pcta.filename = argv[1]
    pcta.setrunningtime(1)  # minutes
    pcta.run()
    pcta.__str__()

if __name__ == "__main__":
    sys.exit(main())
