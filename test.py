import sys
#import requests
from pprint import pprint
from pythonnet import set_runtime
#from requests.auth import HTTPBasicAuth
#rt = get_coreclr(r"C:\Test\MyApp\out_path\MyApp.runtimeconfig.json")
#set_runtime(rt)

import clr



#rt = get_coreclr(r"C:\Test\MyApp\out_path\MyApp.runtimeconfig.json")
#set_runtime(rt)

clr.FindAssembly(".\\SHIT\\CS_GCL\\CS_GCL")
TL = clr.AddReference(".\\SHIT\\CS_GCL\\CS_GCL")
TL2 = clr.AddReference('.\\SHIT\\FrameworkLib')

print (TL)
print(TL.Location)

from GambaExtrasNamespace import TestMethods
#from CS_GCL.ChampionDatabaseNS import ChampionDatabase
#db = ChampionDatabase.Load("C:\\REPOSITORY\\DiscordGamba\\8thDecember21_3_modified_33_1700_2xHsDuplicateInClassAndLowSkillInClass_General.dat")


from CS_GCL.PythonInterface import SimpleInterface
import CS_GCL


my_instance = TestMethods()
a = my_instance.LiveGameJsonDict("euw","Slemp");
if(a==""):
    print("no live game")
else:
    pprint(a)
#GambaExtras.HelloWorld()

si = SimpleInterface("C:\\REPOSITORY\\DiscordGamba\\SHIT\\8thDecember21_3_modified_33_1700_2xHsDuplicateInClassAndLowSkillInClass_General.dat")
print(si.GetChampionWinrate("kaisa"))
print(si.GetChampionWinrate("kaisa",True))

print(list(si.ChampionNames()))
roles = list(si.RolePositions())
print(roles)
#print(si.RolePositions())
list_of_arrays = (list(si.ChampionCounters("kaisa",roles[3].Key)))

py_dict = []
for t in list_of_arrays:
    py_dict.append(str(t[0]) +", " + str(t[1]))

pprint(py_dict)


