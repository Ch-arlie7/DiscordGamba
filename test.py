import sys
#import requests
from clr_loader import get_coreclr
from pythonnet import set_runtime
#from requests.auth import HTTPBasicAuth
#rt = get_coreclr(r"C:\Test\MyApp\out_path\MyApp.runtimeconfig.json")
#set_runtime(rt)

import clr



#rt = get_coreclr(r"C:\Test\MyApp\out_path\MyApp.runtimeconfig.json")
#set_runtime(rt)

clr.FindAssembly("FrameworkLib")
TL = clr.AddReference("FrameworkLib")

#TL = clr.AddReference('GambaExtras')
print (TL)
print(TL.Location)
#from System.Windows.Forms import Form
from GambaExtrasNamespace import TestMethods
my_instance = TestMethods()
a = my_instance.LiveGameJsonDict("euw","MagiFelix5");
print(a)
#GambaExtras.HelloWorld()


