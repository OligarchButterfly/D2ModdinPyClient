'''
Created on 01.06.2014

@author: Schleppi
'''
from unittest import TestCase

from d2mp.core.mods import ModManager, write_to_file
from os import mkdir
from mock import Mock
from tempfile import mkdtemp
from os.path import join, isdir, isfile, basename
import shutil, os
from d2mp.utils.xsockets import XSockets, XSocketsClient
from d2mp.core.connection import ConnectionManager

def new_dota_dir():
    ModManager._dota_path = Mock(return_value = mkdtemp())

class ModTest(TestCase):  
    
    def test_singleton(self):
        man1 = ModManager()
        man2 = ModManager()
         
        self.assertEqual(man1, man2)
        
    def setUp(self):
        new_dota_dir()
        self.manager = ModManager()
#         self.real_method = self.manager._dota_path 
#         self.manager._dota_path = Mock(return_value = mkdtemp())

        self.mod1_folder = join(self.manager._d2mp_path(), "mod1")
        self.mod1_info_file = join(self.mod1_folder, "addoninfo.txt")
        
        self.mod2_folder = join(self.manager._d2mp_path(), "mod2")
        self.mod2_info_file = join(self.mod2_folder, "addoninfo.txt")
        
        
        self.mod_to_delete_folder = join(self.manager._d2mp_path(), "mod_to_delete")
        self.mod_to_delete_info_file = join(self.mod2_folder, "addoninfo.txt")
        
        self.mods = [basename(f) for f in [self.mod1_folder, self.mod2_folder]]
        
        for folder in [self.mod1_folder, self.mod2_folder, self.mod_to_delete_folder]:
            if not isdir(folder): os.mkdir(folder)
        
        for f in [self.mod1_info_file, self.mod2_info_file, self.mod_to_delete_info_file]:
            if not isfile(f): open(f, "w").close()
        
        shutil.rmtree(self.manager._mod_path())
        
    
    def tearDown(self):
        shutil.rmtree(self.manager._d2mp_path())
#         self.manager._dota_path = self.real_method
    
    def test_mod_names(self):
        for mod in self.mods:
            self.assertIn(mod, self.manager.mod_names_as_string(), "mods \"%s\" was not in the mod list!" %(mod))
        
    def test_setting_mod(self):
        mod1_name, mod2_name = self.mods
        
        self.assertNotIn(mod2_name, os.listdir(self.manager._mod_path()), "mod2 should NOT be active now")
        self.assertNotIn(mod1_name, os.listdir(self.manager._mod_path()), "mod1 should NOT be active now")    
        self.manager.set_mod(mod1_name)
        self.assertIn(mod1_name, self.manager.get_active_mod(), "mod1 should be active now")
        
        self.assertNotIn(mod2_name, os.listdir(self.manager._mod_path()), "mod2 should NOT be active now")        
        self.manager.set_mod(mod2_name)
        self.assertIn(mod2_name, self.manager.get_active_mod(), "mod2 should be active now")
        self.assertNotIn(mod1_name, os.listdir(self.manager._mod_path()), "mod1 should NOT be active now")    
        
    def test_active_mod(self):
        mod1_name, mod2_name = self.mods
        self.assertIsNone(self.manager.get_active_mod(), "there should be no active mod")
        
        self.manager.set_mod(mod1_name)
        self.assertEqual(mod1_name, self.manager.get_active_mod(), "mod1 should be active")
        
        self.manager.set_mod(mod2_name)
        self.assertEqual(mod2_name, self.manager.get_active_mod(), "mod1 should be active")
        
        self.manager.delete_mods()
        self.assertIsNone(self.manager.get_active_mod(), "there should be no active mod")
        
    
    def test_deleting_mod(self):
        mod_name = basename(self.mod_to_delete_folder)
        self.assertIn(mod_name, os.listdir(self.manager._d2mp_path()), "mod should be in d2mp folder")
        self.assertIn(mod_name, self.manager.mod_names(), "mod should be in cache")
        self.manager.delete_mod(mod_name)
        self.assertNotIn(mod_name, os.listdir(self.manager._d2mp_path()), "mod should NOT be in d2mp folder")
        self.assertNotIn(mod_name, self.manager.mod_names(), "mod should NOT be in cache")    

    def test_delete_all_mods(self):
        mod1, mod2 = self.mods
        mod3 = basename(self.mod_to_delete_folder)
        
        for mod in [mod1, mod2, mod3]:
            self.assertIn(mod, os.listdir(self.manager._d2mp_path()), "all mods should be present")
            self.assertIn(mod, self.manager.mod_names(), "all mods should be present in cache")
        
        self.manager.delete_mods()
        
        self.assertTrue(len(os.listdir(self.manager._d2mp_path())) == 0, "no mods should be present in d2mp folder anymore")
        self.assertTrue(len(os.listdir(self.manager._mod_path())) == 0, "no mods should be present in mod folder anymore")
        
        self.assertTrue(len(self.manager._mods()) == 0, "no mods should be present in cache anymore")


class ModInstallTest(TestCase):
    def send_reply(self, *args, **kwargs):
        self.manager.signals.message.emit("ready")
    
    def setUp(self):
        new_dota_dir()
        ModManager.install_mod = Mock(side_effect = self.send_reply)
        XSocketsClient.start = Mock()
        ConnectionManager.send = Mock()
         
        self.manager = ModManager()
        self.con = ConnectionManager()
        self.manager.signals.message.connect(self.con.send)
         
    def tearDown(self):
        shutil.rmtree(self.manager._d2mp_path())
         
    def test_install_mod(self):
        self.con.handle_command({"msg": "installmod", "url":"someurl", "Mod": {"name":"mod_name", "version":"mod_version" }})
         
        self.manager.install_mod.assert_called_with("mod_name", "mod_version", "someurl")
        self.con.send.assert_called_with("ready")
    
    
        
class GameInfoTest(TestCase):
    
    def setUp(self):
        self.dota_info_normal = """
            "GameInfo"
            {
              game  "DOTA 2"
              gamelogo 1
              type multiplayer_only
              nomodels 1
              nohimodel 1
              nocrosshair 0
              GameData        "dota.fgd"
              SupportsDX8 0
            
            
              FileSystem
              {
                SteamAppId        816
                ToolsAppId        211
                
                SearchPaths
                {
                  Game        |gameinfo_path|.
                  Game        platform
                }
              }
            }"""
        
        self.dota_info_modded = """
             "GameInfo"
            {
              game  "DOTA 2"
              gamelogo 1
              type multiplayer_only
              nomodels 1
              nohimodel 1
              nocrosshair 0
              GameData        "dota.fgd"
              SupportsDX8 0
            
            
              FileSystem
              {
                SteamAppId        816
                ToolsAppId        211
                
                SearchPaths
                {
                  Game        |gameinfo_path|.
                  Game        platform
                  Game        |gameinfo_path|addons\d2moddin
                }
              }
            }"""
    
        new_dota_dir()
        self.manager = ModManager()
#         self.real_method = self.manager._dota_path 
#         self.manager._dota_path = Mock(return_value = mkdtemp())
        dota_subdir = join(self.manager._dota_path(), "dota")
        if not isdir(dota_subdir): mkdir(dota_subdir)
        write_to_file(self.manager.dota_info_file(), self.dota_info_normal)

#     def tearDown(self):
#         self.manager._dota_path = self.real_method

    def test_is_modded_tester(self):
        write_to_file(self.manager.dota_info_file(), self.dota_info_normal)
        self.assertFalse(self.manager.is_modded(), "should NOT be modded")
        
        write_to_file(self.manager.dota_info_file(), self.dota_info_modded)
        self.assertTrue(self.manager.is_modded(), "should be modded")
        

    def test_mod_game_info(self):
        
        self.assertFalse(self.manager.is_modded(), "game info schould NOT be modded at the beginning")
        
        self.manager.mod_game_info()
        self.assertTrue(self.manager.is_modded(), "game info schould be modded now")
        
    
    def test_unmod_game_info(self):
        self.manager.mod_game_info()
        self.assertTrue(self.manager.is_modded(), "game info schould be modded at the beginning")
        
        self.manager.unmod_game_info()
        self.assertFalse(self.manager.is_modded(), "game info schould NOT be modded anymore")



