# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

import bpy
import bmesh

def save_bmesh(fw, bm, use_color, color_type, material_colors):
    fw('#VRML V2.0 utf8\n')
    fw('#modeled using blender3d http://blender.org\n')
    fw('Shape {\n')
    fw('\tappearance Appearance {\n')
    fw('\t\tmaterial Material {\n')
    fw('\t\t}\n')  # end 'Material'
    fw('\t}\n')  # end 'Appearance'

    fw('\tgeometry IndexedFaceSet {\n')
    fw('\t\tcoord Coordinate {\n')
    fw('\t\t\tpoint [ ')
    v = None
    for v in bm.verts:
        fw("%.6f %.6f %.6f " % v.co[:])
    del v
    fw(']\n')  # end 'point[]'
    fw('\t\t}\n')  # end 'Coordinate'

    if use_color:
        if color_type == 'MATERIAL':
            fw('\t\tcolorPerVertex FALSE\n')
            fw('\t\tcolor Color {\n')
            fw('\t\t\tcolor [ ')
            c = None
            for c in material_colors:
                fw(c)
            del c
            fw(']\n')  # end 'color[]'
            fw('\t\t}\n')  # end 'Color'
        elif color_type == 'VERTEX':
            fw('\t\tcolorPerVertex TRUE\n')
            fw('\t\tcolor Color {\n')
            fw('\t\t\tcolor [ ')
            v = None
            c_none = "0.00 0.00 0.00 "
            color_layer = bm.loops.layers.color.active
            assert(color_layer is not None)
            for v in bm.verts:
                # weak, use first loops color
                try:
                    l = v.link_loops[0]
                except:
                    l = None
                fw(c_none if l is None else ("%.2f %.2f %.2f " % l[color_layer][:]))
                
            del v
            fw(']\n')  # end 'color[]'
            fw('\t\t}\n')  # end 'Color'
    
    if use_color:
        if color_type == 'MATERIAL':
            fw('\t\tcolorIndex [ ')
            i = None
            for f in bm.faces:
                i = f.material_index
                if i >= len(material_colors):
                    i = 0
                fw("%d " % i)
            del i
            fw(']\n')  # end 'colorIndex[]'
        elif color_type == 'VERTEX':
            pass

    fw('\t\tcoordIndex [ ')
    f = fv = None
    for f in bm.faces:
        fv = f.verts[:]
        fw("%d %d %d -1 " % (fv[0].index, fv[1].index, fv[2].index))
    del f, fv
    fw(']\n')  # end 'coordIndex[]'

    fw('\t}\n')  # end 'IndexedFaceSet'
    fw('}\n')  # end 'Shape'


def save_object(fw, obj, use_mesh_modifiers, use_color, color_type):
    
    assert(obj.type == 'MESH')
    
    # TODO use_mesh_modifiers

    me = obj.data
    if obj.mode == 'EDIT':
        bm_orig = bmesh.from_edit_mesh(me)
        bm = bm_orig.copy()
    else:
        bm = bmesh.new()
        bm.from_mesh(me)

    bm.transform(obj.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=True)

    # default empty
    material_colors = []

    if use_color:
        if color_type == 'VERTEX':
            if bm.loops.layers.color.active is None:
                use_color = False
        elif color_type == 'MATERIAL':
            if not me.materials:
                use_color = False
            else:
                material_colors = [
                        "%.2f %.2f %.2f " % (m.diffuse_color[:] if m else (1.0, 1.0, 1.0))
                        for m in me.materials]
        else:
            assert(0)

    material_colors = []
    save_bmesh(fw, bm, use_color, color_type, material_colors)

    bm.free()

def save_object_fp(filepath, obj, use_mesh_modifiers, use_color, color_type):
    file = filepath(filepath)
    save_object(file.write, use_color, color_type)
    file.close()

def save(operator,
         context,
         filepath="",
         use_mesh_modifiers=True,
         use_colors=True,
         color_type='MATERIAL'):

    save_object_fp(filepath, context.object,
                   use_mesh_modifiers, use_color, color_type)

    return {'FINISHED'}

# save_object(open("/test.wrl", 'w', encoding='utf-8').write, bpy.context.object)
