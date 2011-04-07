# -*- coding: utf-8 -*-

import math
from functools import reduce

import bpy
from bpy.props import *
from bpy import context
import mathutils as Math
from mathutils import Matrix, Vector, Quaternion
import mathutils.geometry as geo

import mesh_bevel.va
from mesh_bevel.va import *

SMALL_NUMBER = 1E-8

VERT = 1
EDGE = 2
FACE = 4
DELETE = 8
MIX = 16 # 


class BVert():
    def __init__(self, vec=None, co=None, vi=None, i=None, eai=None, fi=None):
        self.vec = vec # relative
        self.co = co # absolute
        self.i = i
        self.vi = vi
        self.eai = eai # along
        self.fi = fi
        self.ebi = None # bevel
        self.eb2i = None # bevel (in f2)
        self.f2i = None
        self.f = 0 # flag

def bevel(ob, follow, type):
    me = ob.data

    # dict
    vvdict = vert_vert_dict(me, sel=0)
    vedict = vert_edge_dict(me, sel=0)
    vfdict = vert_face_dict(me, sel=0)
    efdict = edge_face_dict(me, sel=0)
    kedict = key_edge_dict(me, sel=0)

    bevelverts = []
    bevelvertindex = len(me.vertices)
    bevelfaces = bfaces = []
    bevelfaces_material = bfmats = []
    # ekparallel: bevelkeysorted
    ekparallel = [[] for e in me.edges]
    vvparallel = [set() for v in me.vertices]

    #
    '''vevparallel = {v.index:{kedict[key]:None for key in vedict[v.index]} \
                   for v in me.vertices}
    '''
    vevparallel = {}
    for v in me.vertices:
        if not v.hide:
            evdict = {}
            for key in vedict[v.index]:
                evdict[kedict[key]] = None
            vevparallel[v.index] = evdict
    # bevel
    vkparallel = {v.index:[] for v in me.vertices}

    vertflags = [0 for v in me.vertices]
    #edgeflags = [e.index for e in me.edges]
    faceflags = [0 for f in me.faces]

    # flag
    for i in range(len(me.vertices)):
        # hidden
        if me.vertices[i].hide:
            continue
        tmp = [0, 0]
        for key in vedict[i]:
            if len(efdict[key]) == 0:
                tmp[0] += 1
            else:
                tmp[1] += 1
        if sum(tmp) == 0:
            vertflags[i] |= VERT
        elif tmp[0] >= 1 and tmp[1] == 0:
            vertflags[i] |= EDGE
        elif tmp[0] == 0 and tmp[1] >= 1:
            vertflags[i] |= FACE
        else:
            vertflags[i] |= MIX
    # flag2
    for e in me.edges:
        if e.key in efdict:
            if len(efdict[e.key]) > 2:
                vertflags[e.key[0]] |= MIX
                vertflags[e.key[1]] |= MIX

    # Face
    for face in me.faces:
        if face.hide:
            continue

        findex = face.index
        material = face.material_index

        vcor = {i:[] for i in face.vertices} #  correspond
        vflags = {i:0 for i in face.vertices}

        edge_keys = face.edge_keys

        # ?
        fverts = list(face.vertices)
        for vindex in fverts:
            vert = me.vertices[vindex]

            if not vert.select:
                continue
            if vertflags[vindex] & MIX:
                continue

            # 
            #connected_edges = [me.edges[kedict[key]] for key in edge_keys
            #                   if key in vedict[vindex]]
            connected_edges = [key for key in edge_keys if vindex in key]
            if connected_edges == [edge_keys[0], edge_keys[-1]]:
                connected_edges.reverse()
            #if edge_keys.index(connected_edges[0]) == 0 and \
            #   edge_keys.index(connected_edges[1]) == len(edge_keys) - 1:
            #    connected_edges.reverse()
            e1, e2 = [me.edges[kedict[key]] for key in connected_edges]

            key1 = e1.key
            key2 = e2.key
            v1i = the_other(key1, vindex)
            v2i = the_other(key2, vindex)
            va0 = vert.co
            va1 = me.vertices[v1i].co # edge1
            va2 = me.vertices[v2i].co # edge2
            vac = face.center
            vr01 = va1 - va0
            vr02 = va2 - va0
            vr0c = vac - va0

            if type == 'vert':
                vflags[vindex] = VERT
            elif e1.select and e2.select:
                tmp = [len(efdict[e1.key]), len(efdict[e2.key])]
                if tmp[0] == 1 and tmp[1] == 1:
                    vflags[vindex] = VERT
                elif tmp[0] == 2 and tmp[1] == 1:
                    ea, eb, vra, vrb = e2, e1, vr02, vr01
                    vflags[vindex] = EDGE
                elif tmp[0] == 1 and tmp[1] == 2:
                    ea, eb, vra, vrb = e1, e2, vr01, vr02
                    vflags[vindex] = EDGE
                else:
                    vflags[vindex] = FACE
            elif not e1.select and not e2.select:
                vflags[vindex] = VERT
            else:
                eb = e1 if e1.select else e2
                if len(efdict[eb.key]) == 1:
                    vflags[vindex] = VERT
                else:
                    vflags[vindex] = EDGE
                    if e1.select:
                        ea, eb, vra, vrb = e2, e1, vr02, vr01
                    else:
                        ea, eb, vra, vrb = e1, e2, vr01, vr02

            if vflags[vindex] == FACE:
                # 
                # 180
                vr010c_cross = vr01.cross(vr0c).normalized()
                angle = vr01.angle(vr02)
                q = Quaternion(vr010c_cross, angle / 2)
                v = vr01 * q
                v.normalized()
                if angle > SMALL_NUMBER:
                    s = math.sin(angle / 2)
                    v *= 1.0 / s
                else:
                    v = Vector((0, 0, 0))
                #co = va0 + v # absolute coordinate
                co = va0.copy()

                bevelvert = BVert(v, co, bevelvertindex,
                                  vindex, e1.index, findex)# e1, e2
                bevelvert.ebi = e2.index
                bevelvert.f = FACE
                bevelverts.append(bevelvert)
                vcor[vindex].append(bevelvert.vi) # == bevelvertindex
                #vflags[vindex] = FACE
                bevelvertindex += 1
            elif vflags[vindex] == VERT:
                # 
                # 
                for ea, eb, v in [(e1, e2, vr01), (e2, e1, vr02)]:
                    vei = vevparallel[vindex][ea.index]
                    if not vei:
                        v = v.copy().normalized()
                        #co = va0 + v
                        co = va0.copy()
                        bevelvert = BVert(v, co, bevelvertindex,
                                          vindex, ea.index, findex)
                        bevelvert.ebi = eb.index # bevel
                        bevelvert.f = VERT
                        bevelverts.append(bevelvert)
                        vevparallel[vindex][ea.index] = bevelvert.vi
                        bevelvertindex += 1
                    else:
                        bevelvert = bevelverts[vei - len(me.vertices)]
                        bevelvert.eb2i = eb.index
                        bevelvert.f2i = findex
                    vcor[vindex].append(bevelvert.vi)
                #vflags[vindex] = VERT
            else:
                # 
                # 
                '''
                if e1.select:
                    ea, eb, vra, vrb = e2, e1, vr02, vr01
                else:
                    ea, eb, vra, vrb = e1, e2, vr01, vr02
                '''
                vra = vra.copy().normalized()
                vrb = vrb.copy().normalized()
                angle = vra.angle(vrb)
                if angle > SMALL_NUMBER:
                    v = vra / math.sin(angle)
                    #co = va0 + v
                else:
                    v = Vector((0, 0, 0))
                co = va0.copy()

                vei = vevparallel[vindex][ea.index]
                if not vei:
                    bevelvert = BVert(v, co, bevelvertindex,
                                      vindex, ea.index, findex)
                    bevelvert.ebi = eb.index # bevel
                    bevelvert.f = EDGE
                    bevelverts.append(bevelvert)
                    vevparallel[vindex][ea.index] = bevelvert.vi
                    bevelvertindex += 1
                else:
                    bevelvert = bevelverts[vei - len(me.vertices)]
                    bevelvert.vec = (v +  bevelvert.vec) / 2 # 
                    #bevelvert.co = va0 + bevelvert.vec
                    bevelvert.eb2i = eb.index
                    bevelvert.f2i = findex
                vcor[vindex].append(bevelvert.vi)
                #vflags[vindex] = EDGE

        # vvparallel
        for k, verts in vcor.items():
            for v in verts:
                vvparallel[k].add(v)

        if sum(vflags.values()) == 0: # 
            continue

        # 
        # flag vflags
        vfl = list(vflags.values())
        vf = (vfl.count(VERT), vfl.count(EDGE), vfl.count(FACE))

        if len(face.vertices) == 4:
            if vf[0] == 1:
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3] # next
                v2 = fverts[v0_i - 2] # diagonal
                v3 = fverts[v0_i - 1] # prev
                if vf == (1, 0, 0):
                    # *** CAUTION *** #
                    #bfaces.append([vcor[v0][0], vcor[v0][1]], v1, v3)
                    #
                    bfaces.append([v1, v3, vcor[v0][0], vcor[v0][1]])
                    bfaces.append([v1, v2, v3])
                    # material
                    bfmats.extend([material, material])
                    # delete
                    vertflags[v0] |= DELETE
                elif vf == (1, 2, 0):
                    if vflags[v1] == EDGE:
                        bfaces.append([vcor[v0][0], vcor[v0][1],
                                       vcor[v1][0], v3])
                        bfaces.append([vcor[v1][0], vcor[v2][0], v3])
                        # material
                        bfmats.extend([material, material])
                        # ekparallel
                        key = [vcor[v1][0], vcor[v2][0]]
                        dkey = tuple(sorted([v1, v2]))
                        ekparallel[kedict[dkey]].append(key)
                        # delete
                        vertflags[v1] |= DELETE
                        vertflags[v2] |= DELETE
                    else:
                        bfaces.append([vcor[v0][0], vcor[v0][1],
                                       v1, vcor[v3][0]])
                        bfaces.append([v1, vcor[v2][0], vcor[v3][0]])
                        # material
                        bfmats.extend([material, material])
                        # ekparallel
                        key = [vcor[v2][0], vcor[v3][0]]
                        dkey = tuple(sorted([v2, v3]))
                        ekparallel[kedict[dkey]].append(key)
                        # delete
                        vertflags[v2] |= DELETE
                        vertflags[v3] |= DELETE
                else:
                    # vf == (1,2,1)
                    bfaces.append([vcor[v0][0], vcor[v0][1],
                                   vcor[v1][0], vcor[v3][0]])
                    bfaces.append([vcor[v1][0], vcor[v2][0], vcor[v3][0]])
                    # material
                    bfmats.extend([material, material])
                    # ekparallel
                    for i, j in [[v1, v2], [v2, v3]]:
                        key = [vcor[i][0], vcor[j][0]]
                        dkey = tuple(sorted([i, j]))
                        ekparallel[kedict[dkey]].append(key)
                    # delete
                    for i in [v1, v2, v3]:
                        vertflags[i] |= DELETE
                # vkparallel
                vkparallel[v0].append([vcor[v0][1], vcor[v0][0]])
                # delete
                vertflags[v0] |= DELETE

            elif vf[0] == 2:
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                if EDGE not in vfl:
                    # vf == (2, 0, 0)
                    if vflags[v1] == VERT:
                        bfaces.append([vcor[v0][0], vcor[v0][1],
                                       vcor[v1][0], vcor[v1][1]])
                        bfaces.append([vcor[v0][0], vcor[v1][1], v2, v3])
                        # material
                        bfmats.extend([material, material])
                        # vkparallel
                        vkparallel[v1].append([vcor[v1][1], vcor[v1][0]])
                        # delete
                        vertflags[v1] |= DELETE
                    elif vflags[v3] == VERT:
                        bfaces.append([vcor[v3][0], vcor[v3][1],
                                       vcor[v0][0], vcor[v0][1]])
                        bfaces.append([vcor[v3][0], vcor[v0][1], v1, v2])
                        bfmats.extend([material, material])
                        # vkparallel
                        vkparallel[v3].append([vcor[v3][1], vcor[v3][0]])
                        # delete
                        vertflags[v3] |= DELETE
                    elif vflags[v2] == VERT: # diagonal
                        bfaces.append([vcor[v0][0], vcor[v0][1], v1, v3])
                        bfaces.append([vcor[v2][0], vcor[v2][1], v3, v1])
                        # material
                        bfmats.extend([material, material])
                        # vkparallel
                        vkparallel[v2].append([vcor[v2][1], vcor[v2][0]])
                        # delete
                        vertflags[v2] |= DELETE
                    # delete
                    vertflags[v0] |= DELETE
                else:
                    # vf == (2, 2, 0)
                    if vflags[v1] == VERT:
                        bfaces.append([vcor[v0][0], vcor[v0][1],
                                       vcor[v1][0], vcor[v1][1]])
                        bfaces.append([vcor[v0][1], vcor[v1][0],
                                       vcor[v2][0], vcor[v3][0]])
                        # material
                        bfmats.extend([material, material])
                        # vkparallel
                        vkparallel[v1].append([vcor[v1][1], vcor[v1][0]])
                        # ekparallel
                        key = [vcor[v2][0], vcor[v3][0]]
                        dkey = tuple(sorted([v2, v3]))
                        ekparallel[kedict[dkey]].append(key)
                    if vflags[v3] == VERT:
                        bfaces.append([vcor[v3][0], vcor[v3][1],
                                       vcor[v0][0], vcor[v0][1]])
                        bfaces.append([vcor[v3][0], vcor[v0][1],
                                       vcor[v1][0], vcor[v2][0]])
                        # material
                        bfmats.extend([material, material])
                        # vkparallel
                        vkparallel[v3].append([vcor[v3][1], vcor[v3][0]])
                        # ekparallel
                        key = [vcor[v1][0], vcor[v2][0]]
                        dkey = tuple(sorted([v1, v2]))
                        ekparallel[kedict[dkey]].append(key)
                    # delete
                    for i in fverts:
                        vertflags[i] |= DELETE
                # vkparallel
                vkparallel[v0].append([vcor[v0][1], vcor[v0][0]])

            elif vf == (3, 0, 0):
                v0 = [k for k, v in vflags.items() if v == 0][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                bfaces.append([v0, vcor[v1][0], vcor[v3][1]])
                bfaces.append([vcor[v1][0], vcor[v1][1],
                               vcor[v3][0], vcor[v3][1]])
                bfaces.append([vcor[v1][1], vcor[v2][0],
                               vcor[v2][1], vcor[v3][0]])
                # material
                bfmats.extend([material, material, material])
                # vkparallel
                for i in [v1, v2, v3]:
                    vkparallel[i].append([vcor[i][1], vcor[i][0]])
                # delete
                for i in [v1, v2, v3]:
                    vertflags[i] |= DELETE

            elif vf == (4, 0, 0):
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                '''
                bfaces.append([vcor[v0][0], vcor[v0][1],
                               vcor[v1][0], vcor[v3][1]])
                bfaces.append([vcor[v1][0], vcor[v1][1],
                               vcor[v3][0], vcor[v3][1]])
                bfaces.append([vcor[v1][1], vcor[v2][0],
                               vcor[v2][1], vcor[v3][0]])
                '''
                bfaces.append([vcor[v0][0], vcor[v0][1],
                               vcor[v1][0], vcor[v1][1]])
                bfaces.append([vcor[v1][1], vcor[v2][0],
                               vcor[v3][1], vcor[v0][0]])
                bfaces.append([vcor[v2][0], vcor[v2][1],
                               vcor[v3][0], vcor[v3][1]])
                # material
                bfmats.extend([material, material, material])
                # vkparallel
                for i in [v0, v1, v2, v3]:
                    vkparallel[i].append([vcor[i][1], vcor[i][0]])
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE

            elif vf == (0, 2, 0):
                v0 = [k for k, v in vflags.items() if v == EDGE][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                if vflags[v1] != EDGE:
                    v0 = fverts[fverts.index(v0) - 1]
                    v1 = fverts[fverts.index(v1) - 1]
                    v2 = fverts[fverts.index(v2) - 1]
                    v3 = fverts[fverts.index(v3) - 1]
                #bfaces.append([vcor[v0][0], vcor[v1][0], v2, v3])
                bfaces.append([v2, v3, vcor[v0][0], vcor[v1][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                key = [vcor[v0][0], vcor[v1][0]]
                dkey = tuple(sorted([v0, v1]))
                ekparallel[kedict[dkey]].append(key)
                # delete
                vertflags[v0] |= DELETE
                vertflags[v1] |= DELETE

            elif vf == (0, 4, 0):
                bfaces.append([vcor[i][0] for i in fverts])
                # material
                bfmats.extend([material])
                # ekparallel
                keys = [(fverts[i - 1], fverts[i]) for i in range(4)]
                selkeys = [key for key in face.edge_keys
                           if me.edges[kedict[key]].select]
                keys = [key for key in keys if tuple(sorted(key)) in selkeys]
                for k in keys:
                    v0, v1 = k
                    key = [vcor[v0][0], vcor[v1][0]]
                    dkey = tuple(sorted([v0, v1]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE

            elif vf == (0, 2, 1):
                v0 = [k for k, v in vflags.items() if v == FACE][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                bfaces.append([vcor[v0][0], vcor[v1][0], v2, vcor[v3][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                for i, j in [[v0, v1], [v3, v0]]:
                    key = [vcor[i][0], vcor[j][0]]
                    dkey = tuple(sorted([i, j]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in [v0, v1, v3]:
                    vertflags[i] |= DELETE

            elif vf == (0, 2, 2):
                v0 = [k for k, v in vflags.items() if v == EDGE][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 3]
                v2 = fverts[v0_i - 2]
                v3 = fverts[v0_i - 1]
                if vflags[v1] != FACE:
                    v0 = fverts[fverts.index(v0) - 3]
                    v1 = fverts[fverts.index(v1) - 3]
                    v2 = fverts[fverts.index(v2) - 3]
                    v3 = fverts[fverts.index(v3) - 3]
                bfaces.append([vcor[i][0] for i in fverts])
                # material
                bfmats.extend([material])
                # ekparallel
                for i, j in [[v0, v1], [v1, v2], [v2, v3]]:
                    key = [vcor[i][0], vcor[j][0]]
                    dkey = tuple(sorted([i, j]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE

            elif vf == (0, 0, 4):
                v0, v1, v2, v3 = fverts
                bfaces.append([vcor[v0][0], vcor[v1][0],
                               vcor[v2][0], vcor[v3][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                for i, j in [[v0, v1], [v1, v2], [v2, v3], [v3, v0]]:
                    key = [vcor[i][0], vcor[j][0]]
                    dkey = tuple(sorted([i, j]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE
            else:
                continue

        else: # Triangle
            if vf == (1, 0, 0):
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                #bfaces.append([vcor[v0][0], vcor[v0][1], v1, v2])
                bfaces.append([v1, v2, vcor[v0][0], vcor[v0][1]])
                # material
                bfmats.extend([material])
                # vkparallel
                vkparallel[v0].append([vcor[v0][1], vcor[v0][0]])
                # delete
                vertflags[v0] |= DELETE
            elif vf == (1, 2, 0):
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([vcor[v0][0], vcor[v0][1],
                               vcor[v1][0], vcor[v2][0]])
                # material
                bfmats.extend([material])
                # vkparallel
                vkparallel[v0].append([vcor[v0][1], vcor[v0][0]])
                # ekparallel
                key = [vcor[v1][0], vcor[v2][0]]
                dkey = tuple(sorted([v1, v2]))
                ekparallel[kedict[dkey]].append(key)
                # delete
                vertflags[v0] |= DELETE
            elif vf == (2, 0, 0):
                v0 = [k for k, v in vflags.items() if v == 0][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([v0, vcor[v1][0], vcor[v2][1]])
                bfaces.append([vcor[v1][0], vcor[v1][1],
                               vcor[v2][0], vcor[v2][1]])
                # material
                bfmats.extend([material, material])
                # vkparallel
                for i in [v1, v2]:
                    vkparallel[i].append([vcor[i][1], vcor[i][0]])
                # delete
                vertflags[v1] |= DELETE
                vertflags[v2] |= DELETE
            elif vf == (3, 0, 0):
                v0 = [k for k, v in vflags.items() if v == VERT][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([vcor[v0][0], vcor[v0][1],
                               vcor[v1][0], vcor[v2][1]])
                bfaces.append([vcor[v1][0], vcor[v1][1],
                               vcor[v2][0], vcor[v2][1]])
                # material
                bfmats.extend([material, material])
                # vkparallel
                for i in [v0, v1, v2]:
                    vkparallel[i].append([vcor[i][1], vcor[i][0]])
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE
            elif vf == (0, 2, 0):
                v0 = [k for k, v in vflags.items() if v == 0][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([v0, vcor[v1][0], vcor[v2][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                key = [vcor[v1][0], vcor[v2][0]]
                dkey = tuple(sorted([v1, v2]))
                ekparallel[kedict[dkey]].append(key)
                # delete
                vertflags[v1] |= DELETE
                vertflags[v2] |= DELETE
            elif vf == (0, 2, 1):
                v0 = [k for k, v in vflags.items() if v == FACE][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([vcor[v0][0], vcor[v1][0], vcor[v2][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                for i, j in [[v0, v1], [v2, v0]]:
                    key = [vcor[i][0], vcor[j][0]]
                    dkey = tuple(sorted([i, j]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE
            elif vf == (0, 0, 3):
                v0 = [k for k, v in vflags.items() if v == FACE][0]
                v0_i = fverts.index(v0)
                v1 = fverts[v0_i - 2]
                v2 = fverts[v0_i - 1]
                bfaces.append([vcor[v0][0], vcor[v1][0], vcor[v2][0]])
                # material
                bfmats.extend([material])
                # ekparallel
                for i, j in [[v0, v1], [v1, v2], [v2, v0]]:
                    key = [vcor[i][0], vcor[j][0]]
                    dkey = tuple(sorted([i, j]))
                    ekparallel[kedict[dkey]].append(key)
                # delete
                for i in fverts:
                    vertflags[i] |= DELETE
            else:
                continue

        # delete
        faceflags[findex] |= DELETE

    # active material
    if ob.active_material in list(me.materials):
        actmat = list(me.materials).index(ob.active_material)
    else:
        actmat = None

    # bevel
    for eindex, edges in enumerate(ekparallel):
        #if edges:
        if len(edges) == 2: # 
            v0, v1 = edges[0] # 
            v2, v3 = edges[1]
            #bfaces.append([v3, v2, v1, v0]) # 
            bfaces.append([v1, v0, v3, v2]) # 
            # material
            key = me.edges[eindex].key
            fmats = [me.faces[i].material_index for i in efdict[key]]
            samemat = True
            fmat = fmats[0]
            for i in fmats:
                if i != fmat:
                    samemat = False
            if samemat:
                bfmats.extend([fmat])
            else:
                bfmats.extend([actmat])

            # add new keys to vkparallel
            key1 = (v1, v2)
            key2 = (v3, v0)
            for v in me.edges[eindex].key:
                vv_verts = vvparallel[v]
                if key1[0] in vv_verts or key1[1] in vv_verts:
                    vkparallel[v].append(key1)
                else:
                    vkparallel[v].append(key2)

    # bevel(flag:VERT)
    # vkparallelkey
    for vi, keys in vkparallel.items():
        if len(keys) < 2:
            continue

        verts = keypath(keys)
        if not verts:
            continue

        if len(verts) <= 4:
            bfaces.append(verts)
            # material
            #bfmats.extend([actmat])
        else:
            faces = fill(verts)
            bfaces.extend(faces)
            # material
            #bfmats.extend([actmat for i in range(len(faces))])

        # material
        fmats = [me.faces[i].material_index for i in vfdict[vi]]
        samemat = True
        fmat = fmats[0]
        for i in fmats:
            if i != fmat:
                samemat = False
        if len(verts) <= 4:
            fnum = 1
        else:
            fnum = len(faces)
        if samemat:
            bfmats.extend([fmat for i in range(fnum)])
        else:
            bfmats.extend([actmat for i in range(fnum)])

    # edge
    beveledges = bedges = []
    '''vevparallel = {v.index:{kedict[key]:None for key in vedict[v.index]}
                   for v in me.vertices if len(vedict[v.index]) == 2}
    '''
    vevparallel = {}
    for v in me.vertices:
        if v.hide:
            continue
        if v.index not in vedict:
            continue
        if len(vedict[v.index]) == 2:
            evdict = {}
            for key in vedict[v.index]:
                evdict[kedict[key]] = None
            vevparallel[v.index] = evdict

    for vertex in me.vertices:
        vindex = vertex.index
        if not vertex.select or vertex.hide:
            continue
        if not vertflags[vindex] & EDGE:
            continue

        keys = vedict[vindex]
        if len(keys) != 2:
            continue

        e1 = me.edges[kedict[keys[0]]]
        e2 = me.edges[kedict[keys[1]]]
        if e1.hide or e2.hide:
            continue

        everts = []
        va0 = me.vertices[vindex].co
        for edge in [e1, e2]:
            va1 = me.vertices[the_other(edge.key, vindex)].co
            vr01 = va1 - va0
            vr01.normalized()
            v = vr01
            co = va0.copy()
            bevelvert = BVert(v, co, bevelvertindex,
                              vindex, edge.index, None)
            bevelvert.f = VERT
            bevelverts.append(bevelvert)
            vevparallel[vindex][edge.index] = bevelvert.vi
            everts.append(bevelvert.vi)
            bevelvertindex += 1
        bedges.append(sorted(everts)) # sorted
        # delete
        vertflags[vindex] |= DELETE

    for edge in me.edges:
        conti = 0
        for i in edge.key:
            v = me.vertices[i]
            #if not v.select or v.hide or not vertflags[vindex] & EDGE:
            if (not v.select) or v.hide or (not vertflags[i] & EDGE):
                conti =+ 1
        if conti == 2:
            continue

        v1, v2 = edge.key
        vb1 = vevparallel[v1][edge.index] if v1 in vevparallel else v1
        vb2 = vevparallel[v2][edge.index] if v2 in vevparallel else v2
        if vb1 and vb2:
            bedges.append(sorted([vb1, vb2]))

    # delverts
    delverts = [i for i, v in enumerate(vertflags) if v & DELETE]

    # delfaces
    #delfaces = [f for f in faceflags if f & DELETE]

    #return bevelverts, beveledges, bevelfaces, delverts, delfaces
    return bevelverts, beveledges, bevelfaces, delverts, bfmats

class Bevel(bpy.types.Operator):
    bl_label = 'Bevel'
    bl_idname = 'mesh.bevel'
    bl_options = {'REGISTER', 'UNDO'}

    #bpy.data.window_managers['WinMan'].operators['Test'].v2

    dist = FloatProperty(name='Dist',
                         description = 'tool tip ?',
                         default = 0.0,
                         min = 0.0,
                         max = 10.0,
                         soft_min = 0.0,
                         soft_max = 10.0,
                         step = 1,
                         precision = 3,
                         subtype = 'DISTANCE',
                         unit = 'LENGTH')
    follow = BoolProperty(name = 'Follow edge',
                          description = 'disable item. hidden',
                          default=True,
                          options = {'HIDDEN'})
    type = EnumProperty(items = (('def', 'Default', ''),
                                 ('vert', 'Vertex', '')),
                        name="Bevel type",
                        description="",
                        default='def')

    @classmethod
    def poll(cls, context):
        if context.active_object:
            return context.active_object.mode == 'EDIT'
        else:
            return False

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        #bpy.ops.object.editmode_toggle()

        dist = self.dist
        follow = self.follow
        type = self.type

        p = self.p

        ob = context.active_object
        mesh_mode = list(bpy.context.tool_settings.mesh_select_mode)
        if not mesh_mode[0]:
            bpy.context.tool_settings.mesh_select_mode[0] = True

        if follow != p.follow or type != p.type:
            print('recalc')
            bevelverts, beveledges, bevelfaces, delverts, bfmats = bevel(ob, follow, type)
            p.follow = follow
            p.type = type
            p.data = [bevelverts, beveledges, bevelfaces, delverts, bfmats]
        else:
            bevelverts, beveledges, bevelfaces, delverts, bfmats = p.data

        me = ob.data
        vnum = len(me.vertices)
        enum = len(me.edges)
        fnum = len(me.faces)

        # add
        add_edges_num = len(beveledges)
        for i in bevelfaces:
            add_edges_num += len(i)
        #me.add_geometry(len(bevelverts), add_edges_num, len(bevelfaces))
        me.vertices.add(len(bevelverts))
        me.edges.add(add_edges_num)
        me.faces.add(len(bevelfaces))
        # vert
        for i in range(len(bevelverts)):
            vert = bevelverts[i]
            me.vertices[vnum + i].co = vert.co + vert.vec * dist
        # edge
        for i in range(len(beveledges)):
            me.edges[enum + i].vertices = beveledges[i]
        # face
        for i in range(len(bevelfaces)):
            verts = bevelfaces[i]
            if len(bevelfaces[i]) == 4:
                if verts[-1] != 0:
                    me.faces[fnum + i].vertices_raw = verts
                else:
                    me.faces[fnum + i].vertices_raw = [verts[i] for i in range(-1, 3, 1)]
            elif len(bevelfaces[i]) == 3:
                #me.faces[fnum + i].vertices_raw = bevelfaces[i] + [bevelfaces[i][-1]]
                me.faces[fnum + i].vertices_raw = verts + [0]
            if bfmats[i]:
                me.faces[fnum + i].material_index = bfmats[i]
        # update
        me.update(calc_edges=True) # calc_edges=True

        # delete
        for v in me.vertices:
            if not v.hide:
                v.select = 0
        for i in delverts:
            me.vertices[i].select = 1
        bpy.ops.object.mode_set(mode='EDIT')
        #bpy.ops.mesh.delete()
        delstate = bpy.ops.mesh.delete(type='VERT')

        # check index
        bpy.ops.object.mode_set(mode='OBJECT')
        delnum = len(delverts)
        vecs = {}
        for cnt, v in enumerate(bevelverts):
            vecs[vnum + cnt - delnum] = v.vec
        # select
        for i in vecs.keys():
            me.vertices[i].select = 1
        bpy.ops.object.mode_set(mode='EDIT')

        if not mesh_mode[0]:
            bpy.context.tool_settings.mesh_select_mode[:] = mesh_mode[:]

        return {'FINISHED'}
        #print(dist)
        #return {'PASS_THROUGH'}

    def invoke(self, context, event):
        context.area.tag_redraw()

        self.p = p = NullClass()
        p.dist = p.follow = p.type = p.data = None

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        self.execute(context)

        return {'FINISHED'}
        #RUNNING_MODAL, CANCELLED, FINISHED, PASS_THROUGH

