# AlingTools.py (c) 2009, 2010 Gabriel Beaudin (gabhead)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_addon_info = {
    'name': '3D View: Align Tools',
    'author': 'Gabriel Beaudin (gabhead)',
    'version': (0,13),
    'blender': (2, 5, 4),
    'location': 'Tool Shelf',
    'description': 'Align selected objects to the active object',
    'wiki_url':
    'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/3D interaction/Align_Tools',
    'tracker_url': 'https://projects.blender.org/tracker/index.php?'\
        'func=detail&aid==22389&group_id=153&atid=468',
    'category': '3D View'}


import bpy
from bpy.props import *
#import Mathutils
sce = bpy.context.scene

##interface
######################

class AlignUi(bpy.types.Panel):
    bl_label = "Align Tools"
    bl_context = "objectmode"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    def draw(self, context):
        layout = self.layout
        obj = bpy.context.object
        sce = bpy.context.scene
        items_list = [("Min", "Minimum", "Minimum"),
                  ("Max", "Maximum", "Maximum",),
                  ("Center","Center","Center"),
                  ("Origin","Origin","Origin")]

        bpy.types.Scene.SrcLocation = EnumProperty(name="SrcLocation",
                                 items=items_list,
                                 description="SrcLocation",
                                 default="Origin")

        items_list = [("Min", "Minimum", "Minimum"),
                  ("Max", "Maximum", "Maximum",),
                  ("Center","Center","Center"),
                  ("Origin","Origin","Origin")]

        bpy.types.Scene.ActLocation = EnumProperty(
                                 name="ActLocation",
                                 items=items_list,
                                 description="ActLocation",
                                 default="Origin")

        bpy.types.Scene.Aling_LocationX = BoolProperty(
            name="Aling_LocationX",
            attr="Aling_LocationX",
            description="Aling_LocationX",
            default=0)

        bpy.types.Scene.Aling_LocationY=BoolProperty(
            name="Aling_LocationY",
            attr="Aling_LocationY",
            description="Aling_LocationY",
            default=0)

        bpy.types.Scene.Aling_LocationZ=BoolProperty(
            name="Aling_LocationZ",
            attr="Aling_LocationZ",
            description="Aling_LocationZ",
            default=0)

        bpy.types.Scene.Aling_RotationX=BoolProperty(
            name="Aling_RotationX",
            attr="Aling_RotationX",
            description="Aling_LocationX",
            default=0)

        bpy.types.Scene.Aling_RotationY=BoolProperty(
            name="Aling_RotationY",
            attr="Aling_RotationY",
            description="Aling_LocationY",
            default=0)

        bpy.types.Scene.Aling_RotationZ=BoolProperty(
            name="Aling_RotationZ",
            attr="Aling_RotationZ",
            description="Aling_LocationZ",
            default=0)

        bpy.types.Scene.Aling_ScaleX=BoolProperty(
            name="Aling_ScaleX",
            attr="Aling_ScaleX",
            description="Aling_LocationX",
            default=0)

        bpy.types.Scene.Aling_ScaleY=BoolProperty(
            name="Aling_ScaleY",
            attr="Aling_ScaleY",
            description="Aling_LocationY",
            default=0)

        bpy.types.Scene.Aling_ScaleZ=BoolProperty(
            name="Aling_ScaleZ",
            attr="Aling_ScaleZ",
            description="Aling_LocationZ",
            default=0)

        if len(bpy.context.selected_objects)>1:
            
            col = layout.column()
            bo = layout.box()
            bo.prop_menu_enum(data=sce,property="SrcLocation",text=str((len(bpy.context.selected_objects))-1)+" objects: "+sce.SrcLocation,icon='OBJECT_DATA')
            if bpy.context.object != None:
                bo.prop_menu_enum(data=sce,property="ActLocation",text="To: "+obj.name+": "+sce.ActLocation,icon='OBJECT_DATA')

            col = layout.column()
            col.label(text="Align Location:", icon='MAN_TRANS')
        		
            col = layout.column_flow(columns=3,align=True)
            col.prop(sce,"Aling_LocationX",text="X")
            col.prop(sce,"Aling_LocationY",text="Y")
            col.prop(sce,"Aling_LocationZ",text="Z")

            col = layout.column()
            col.label(text="Align Rotation:", icon='MAN_ROT')

            col = layout.column_flow(columns=3,align=True)
            col.prop(sce,"Aling_RotationX",text="X")
            col.prop(sce,"Aling_RotationY",text="Y")
            col.prop(sce,"Aling_RotationZ",text="Z")

            col = layout.column()
            col.label(text="Align Scale:", icon='MAN_SCALE')

            col = layout.column_flow(columns=3,align=True)
            col.prop(sce,"Aling_ScaleX",text="X")
            col.prop(sce,"Aling_ScaleY",text="Y")
            col.prop(sce,"Aling_ScaleZ",text="Z")

            col = layout.column(align=False)
            col.operator("object.AlignObjects",text="Align")
##Methods
##################

##Get World Verts location

def VertCoordSysLocalToWorld(obj):
    NewList = []

    for i in obj.data.vertices:
        WorldVert=(obj.matrix_world*i.co)-obj.location
        NewList.append(WorldVert)
    return NewList

##Create World bound_box
def CreateWorldBoundBox(obj):
    World_bound_box = []
    Xlist=[]
    Ylist=[]
    Zlist=[]
    
    #separate X Y and Z
    for i in VertCoordSysLocalToWorld(obj):
        Xlist.append(i.x)
        Ylist.append(i.y)
        Zlist.append(i.z)
    
    # Sort all values
    Xlist = sorted(Xlist)
    Ylist = sorted(Ylist)
    Zlist = sorted(Zlist)
    # assing Minimum and maximum values
    Xmin = Xlist[0]
    Xmax = Xlist[-1]
    Ymin = Ylist[0]
    Ymax = Ylist[-1]
    Zmin = Zlist[0]
    Zmax = Zlist[-1]
    World_bound_box = [Xmin,Xmax,Ymin,Ymax,Zmin,Zmax]
    return World_bound_box
##Align
def main(context):
    sce = bpy.context.scene
    obj = bpy.context.object
    The_i_OffSet=[]
    TheActiveObjOffset=[]
    activeObjWorldBoundBox = CreateWorldBoundBox(obj)
    
    for i in bpy.context.selected_objects:
        if i != obj:
            
            i_World_bound_box = CreateWorldBoundBox(i)
            i_minX = i_World_bound_box[0]
            i_maxX = i_World_bound_box[1]
            i_minY = i_World_bound_box[2]
            i_maxY = i_World_bound_box[3]
            i_minZ = i_World_bound_box[4]
            i_maxZ = i_World_bound_box[5]
            Act_minX = activeObjWorldBoundBox[0]
            Act_maxX = activeObjWorldBoundBox[1]
            Act_minY = activeObjWorldBoundBox[2]
            Act_maxY = activeObjWorldBoundBox[3]
            Act_minZ = activeObjWorldBoundBox[4]
            Act_maxZ = activeObjWorldBoundBox[5]
            imin = [i_minX,i_minY,i_minZ]
            imax = [i_maxX,i_maxY,i_maxZ]
            actmin = [Act_minX,Act_minY,Act_minZ]
            actmax = [Act_maxX,Act_maxY,Act_maxZ]
            
            if sce.SrcLocation == "Min":
                The_i_OffSet = imin
            if sce.SrcLocation == "Max":
                The_i_OffSet = imax
            if sce.SrcLocation == "Center":
                i.location = [0,0,0]
                iCenterX = ((imin[0]+imax[0])/2.0)
                iCenterY = ((imin[1]+imax[1])/2.0)
                iCenterZ = ((imin[2]+imax[2])/2.0)
                
                The_i_OffSet = [iCenterX,iCenterY,iCenterZ]
            if sce.SrcLocation == "Origin":
                The_i_OffSet = [0,0,0]
            
            if sce.ActLocation == "Min":
                TheActiveObjOffset = actmin
            if sce.ActLocation == "Max":
                TheActiveObjOffset = actmax
            if sce.ActLocation == "Center":
                CenterX = ((actmin[0]+actmax[0])/2.0)
                CenterY = ((actmin[1]+actmax[1])/2.0)
                CenterZ = ((actmin[2]+actmax[2])/2.0)
                TheActiveObjOffset = [CenterX,CenterY,CenterZ]
            if sce.ActLocation == "Origin":
                TheActiveObjOffset = [0,0,0]
            
            #Locations
            if sce.Aling_LocationX == True:
                i.location.x = (obj.location[0] + The_i_OffSet[0] + TheActiveObjOffset[0])
            if sce.Aling_LocationY == True:
                i.location.y = (obj.location[1] + The_i_OffSet[1] + TheActiveObjOffset[1])
            if sce.Aling_LocationZ == True:
                i.location.z = (obj.location[2] + The_i_OffSet[2] + TheActiveObjOffset[2])
            #Rotations
            if sce.Aling_RotationX == True:
                i.rotation_euler.x = bpy.context.active_object.rotation_euler.x
            if sce.Aling_RotationY == True:
                i.rotation_euler.y = bpy.context.active_object.rotation_euler.y
            if sce.Aling_RotationZ == True:
                i.rotation_euler.z = bpy.context.active_object.rotation_euler.z
            #Scales
            if sce.Aling_ScaleX == True:
                i.scale.x = bpy.context.active_object.scale.x
            if sce.Aling_ScaleY == True:
                i.scale.y = bpy.context.active_object.scale.y
            if sce.Aling_ScaleZ == True:
                i.scale.z = bpy.context.active_object.scale.z
    
## Classes Op
## Align
class AlignOperator(bpy.types.Operator):
    bl_idname = "object.AlignObjects"
    bl_label = "Align Selected To Active"
    
    @classmethod
    def poll(self, context):
        return context.active_object != None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    pass


def unregister():
    pass


if __name__ == "__main__":
    register()