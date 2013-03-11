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
import os

def save_bmesh(fw, bm,
               use_color, color_type, material_colors,
               use_uv, uv_image):
    fw('#VRML V2.0 utf8\n')
    fw('#modeled using blender3d http://blender.org\n')
    fw('Shape {\n')
    fw('\tappearance Appearance {\n')
    if use_uv:
        fw('\t\ttexture ImageTexture {\n')
        fw('\t\t\turl "%s"\n' % os.path.basename(uv_image.filepath))
        fw('\t\t}\n')  # end 'ImageTexture'
    else:
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

        # ---

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

    if use_uv:
        fw('\t\ttexCoord TextureCoordinate {\n')
        fw('\t\t\tpoint [ ')
        v = None
        uv_layer = bm.loops.layers.uv.active
        assert(uv_layer is not None)
        for f in bm.faces:
            for l in f.loops:
                fw("%.4f %.4f " % l[uv_layer].uv[:])

        del f
        fw(']\n')  # end 'point[]'
        fw('\t\t}\n')  # end 'TextureCoordinate'

        # ---

        fw('\t\ttexCoordIndex [ ')
        i = None
        for i in range(0, len(bm.faces) * 3, 3):
            fw("%d %d %d -1 " % (i, i + 1, i + 2))
        del i
        fw(']\n')  # end 'coordIndex[]'

    fw('\t\tcoordIndex [ ')
    f = fv = None
    for f in bm.faces:
        fv = f.verts[:]
        fw("%d %d %d -1 " % (fv[0].index, fv[1].index, fv[2].index))
    del f, fv
    fw(']\n')  # end 'coordIndex[]'

    fw('\t}\n')  # end 'IndexedFaceSet'
    fw('}\n')  # end 'Shape'


def detect_default_image(obj, bm):
    tex_layer = bm.faces.layers.tex.active
    if tex_layer is not None:
        for f in bm.faces:
            image = f[tex_layer].image
            if image is not None:
                return image
    for m in obj.data.materials:
        if m is not None:
            # backwards so topmost are highest priority
            for mtex in reversed(mat.texture_slots):
                if mtex and mtex.use_map_color_diffuse:
                    texture = mtex.texture
                    if texture and texture.type == 'IMAGE':
                        image = texture.image
                        if image is not None:
                            return image
    return None


def save_object(fw, scene, obj,
                use_mesh_modifiers,
                use_color, color_type,
                use_uv):

    assert(obj.type == 'MESH')

    if use_mesh_modifiers:
        is_editmode = (obj.mode == 'EDIT')
        if is_editmode:
            bpy.ops.object.editmode_toggle()

        me = obj.to_mesh(scene, True, 'PREVIEW', calc_tessface=False)
        bm = bmesh.new()
        bm.from_mesh(me)

        if is_editmode:
            bpy.ops.object.editmode_toggle()
    else:
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
    uv_image = None

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

    if use_uv:
        if bm.loops.layers.uv.active is None:
            use_uv = False
        uv_image = detect_default_image(obj, bm)
        if uv_image is None:
            use_uv = False

    material_colors = []
    save_bmesh(fw, bm,
               use_color, color_type, material_colors,
               use_uv, uv_image)

    bm.free()

def save_object_fp(filepath, scene, obj,
                   use_mesh_modifiers,
                   use_color, color_type,
                   use_uv):
    file = open(filepath, 'w', encoding='utf-8')
    save_object(file.write, scene, obj,
                use_mesh_modifiers,
                use_color, color_type,
                use_uv)
    file.close()

def save(operator,
         context,
         filepath="",
         use_mesh_modifiers=True,
         use_color=True,
         color_type='MATERIAL',
         use_uv=True):

    save_object_fp(filepath, context.scene, context.object,
                   use_mesh_modifiers,
                   use_color, color_type,
                   use_uv)

    return {'FINISHED'}
