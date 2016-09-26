import bpy
op = bpy.context.active_operator

op.x_eq = 'a*cos(u)*cos(v)*1.6'
op.y_eq = 'a*sin(u)*cos(v)'
op.z_eq = '2*sin(v)'
op.range_u_min = 0.0
op.range_u_max = 3.140000104904175
op.range_u_step = 32
op.wrap_u = True
op.range_v_min = 0.0
op.range_v_max = 1.0
op.range_v_step = 32
op.wrap_v = False
op.close_v = True
op.n_eq = 1
op.a_eq = '4*cos(v)*pow(sin(fabs(u)),fabs(u))'
op.b_eq = '0'
op.c_eq = '0'
op.f_eq = '0'
op.g_eq = '0'
op.h_eq = '0'
