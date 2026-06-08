from pyefis.user.blake_pfd.airdata_calculations import *

print()

print("IAS:", indicated_airspeed_from_dp(250))
print("Altitude:", pressure_altitude(101325))

print()