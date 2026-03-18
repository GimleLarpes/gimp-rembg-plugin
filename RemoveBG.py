#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#   GIMP - The GNU Image Manipulation Program
#   Copyright (C) 1995 Spencer Kimball and Peter Mattis
#
#   gimp-tutorial-plug-in.py
#   sample plug-in to illustrate the Python plug-in writing tutorial
#   Copyright (C) 2023 Jacob Boerema
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os, string, tempfile
import platform
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gio


def N_(message): return message
def _(message): return GLib.dgettext(None, message)
    
tupleModel = ("u2net","u2net_human_seg", "u2net_cloth_seg", "u2netp", "silueta", "isnet-general-use", "isnet-anime")

def pdbCall(procedureName, args):
    pdb_proc   = Gimp.get_pdb().lookup_procedure(procedureName)
    pdb_config = pdb_proc.create_config()
    for x in args:
        pdb_config.set_property(x, args[x])
    return pdb_proc.run(pdb_config)

def store_layer_png(image, drawable, path):
    interlace, compression = 0, 2

    _, x, y = drawable.get_offsets()
    width, height = drawable.get_width(), drawable.get_height()
    tmp_img = Gimp.Image.new(width, height, image.get_base_type())
    drawable.set_offsets(0, 0)
    tmp_layer = Gimp.Layer.new_from_drawable (drawable, tmp_img)
    tmp_img.insert_layer (tmp_layer, None, 0)
    drawable.set_offsets(x, y)
    
    args = {
      "run-mode": Gimp.RunMode.NONINTERACTIVE,
      "image": tmp_img,
      "file": Gio.File.new_for_path(path),
      "options": None,
      "interlaced": interlace,
      "compression": compression,
      "bkgd": True,
      "offs": False,
      "phys": True,
      "time": True,
      "save-transparent": True
    }
    pdbCall('file-png-export', args);

    tmp_img.delete()
    
def store_layer_jpg(image, drawable, path):
    _, x, y = drawable.get_offsets()
    width, height = drawable.get_width(), drawable.get_height()
    tmp_img = Gimp.Image.new(width, height, image.get_base_type())
    drawable.set_offsets(0, 0)
    tmp_layer = Gimp.Layer.new_from_drawable (drawable, tmp_img)
    tmp_img.insert_layer (tmp_layer, None, 0)
    drawable.set_offsets(x, y)
    
    args = {
      "run-mode": Gimp.RunMode.NONINTERACTIVE,
      "image": tmp_img,
      "file": Gio.File.new_for_path(path),
      "options": None,
      "quality": 0.95,
      "smoothing": 0,
      "optimize": True
    }
    pdbCall('file-jpeg-export', args);
    
    tmp_img.delete()

def RemoveBG(procedure, run_mode, image, drawables, config, data):
    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('plug-in-RemoveBG-python')

        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        # dialog.fill(None)
        dialog.fill(["asMask"])
        dialog.fill(["AlphaMatting"])
        dialog.fill(["aeValue"])
        dialog.get_int_combo("selModel", GimpUi.IntStore.new (tupleModel))
        dialog.fill(["selModel"])
        if not dialog.run():
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            
    removeTmpFile = False#True
    OutputMessage = True#False
    osName = platform.system()
    exportSep = str(os.sep)
    tdir = tempfile.gettempdir()
    if OutputMessage:
        Gimp.message(tdir)
    jpgFile = "%s%sTemp-gimp-0000.jpg" % (tdir, exportSep)
    pngFile = "%s%sTemp-gimp-0000.png" % (tdir, exportSep)
    errFile = "%s%sErrMsg.txt" % (tdir, exportSep)
    x1 = 0
    y1 = 0
    option = ""
    
    Gimp.progress_init("AI Remove background ...")
    Gimp.progress_update(0.0)
            
    asMask       = config.get_property('asMask')
    AlphaMatting = config.get_property('AlphaMatting')
    aeValue      = config.get_property('aeValue')
    selModel     = config.get_property('selModel')
    
    if OutputMessage:
        msg = "data: %s %s %d %s" % (asMask, AlphaMatting, aeValue, tupleModel[selModel])
        Gimp.message(msg)
    
    aiExe = "C:\\Users\\gimle\\AppData\\Local\\Programs\\Python\\Python310\\Scripts\\rembg.exe"
    if OutputMessage:
        Gimp.message(aiExe)
    if AlphaMatting:
        option = "-a -ae %d" % (aeValue)
        
    cmd = '""%s" i -m %s %s "%s" "%s""' % (aiExe, tupleModel[selModel], option, jpgFile, pngFile)
    if OutputMessage:
        Gimp.message(cmd)
        
    Gimp.progress_update(0.1)
    
    Gimp.context_push()
    image.undo_group_start()
    
    drawable = drawables[0]
    curLayer = drawable
    _, x1, y1 = drawable.get_offsets()
    Gimp.progress_update(0.2)
    
    store_layer_jpg(image, drawable, jpgFile)
    Gimp.progress_update(0.4)
    
    ret = os.system(cmd + ' 2> ' + errFile)
    Gimp.progress_update(0.8)
    if OutputMessage:
        if os.path.exists(errFile):
            fp = open(errFile, "r")
            output = fp.read()
            # if len(output) > 0:
                # unicodestr = output.decode('cp950').encode('utf-8')
            fp.close()
            os.remove(errFile)
            if len(output) > 0:
                # Gimp.message(unicodestr)
                Gimp.message(output)

    Gimp.progress_update(0.9)
    file_exists = os.path.exists(pngFile)
    if file_exists:
        args = {
          "run-mode": Gimp.RunMode.NONINTERACTIVE,
          "image": image,
          "file": Gio.File.new_for_path(pngFile)
        }
        result = pdbCall('gimp-file-load-layer', args);
        if (result.index(0) == Gimp.PDBStatusType.SUCCESS):
            gimp_layer = result.index(1)
            gimp_layer.set_offsets(x1, y1)
            image.insert_layer(gimp_layer, drawable.get_parent(),
                           image.get_item_position(drawable))
            if asMask:
                image.select_item(2, gimp_layer)
                image.remove_layer(gimp_layer)
                copyLayer = Gimp.Layer.copy(curLayer)
                image.insert_layer(copyLayer, drawable.get_parent(),
                           image.get_item_position(drawable))
                mask=copyLayer.create_mask(4)
                copyLayer.add_mask(mask)
                Gimp.Selection.none(image)
        else:
            print("Error loading layer from openraster image.")
    
    Gimp.displays_flush()
    image.undo_group_end()
    Gimp.context_pop()
    
    if removeTmpFile:
        if osName == "Windows":
            del_command = "del \"%s%sTemp-gimp-0000.*\"" % (tdir, exportSep)
        else:
            del_command = "rm %s%sTemp-gimp-0000.*" % (tdir, exportSep)
        os.system(del_command)

    Gimp.progress_update(1.0)
    Gimp.progress_end()
    
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

class AIRemoveBG (Gimp.PlugIn):
    def do_query_procedures(self):
        return [ "plug-in-RemoveBG-python" ]

    def do_set_i18n (self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                            RemoveBG, None)

        procedure.set_image_types("*")

        procedure.set_menu_label("AI Remove background ...")
        procedure.add_menu_path('<Image>/Tools/')

        procedure.set_documentation("AI Remove image background",
                                    "AI Remove image background for GIMP 3.0",
                                    name)
        procedure.set_attribution("Gimle Larpes", "Gimle Larpes", "2025")
        
        procedure.add_boolean_argument ("asMask", _("As mask"), _("As mask"),
                                       True, GObject.ParamFlags.READWRITE)
        procedure.add_boolean_argument ("AlphaMatting", _("Alpha matting"), _("Alpha matting"),
                                       False, GObject.ParamFlags.READWRITE)
        procedure.add_int_argument ("aeValue", _("Alpha matting erode size"), _("Alpha matting erode size"),
                                       1, 100, 15, GObject.ParamFlags.READWRITE)
        procedure.add_int_argument ("selModel", _("Model"), _("Model"),
                                       0, len(tupleModel), 0, GObject.ParamFlags.READWRITE)

        return procedure

Gimp.main(AIRemoveBG.__gtype__, sys.argv)
