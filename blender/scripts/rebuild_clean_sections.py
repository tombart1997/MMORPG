"""Clean geometry for surfaces neural reconstruction cannot resolve.

The fern's seven curved fronds and paired leaflets are rebuilt from the reviewed
front/overhead sheet. No geometry or textures from the previous game are used.
"""
import bpy,json,math,random,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]

def material(name,color,metal=0,rough=.8):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=m.diffuse_color
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    m.use_backface_culling=False
    return m

def dead_tree():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bark=material('DeadBark',(.18,.091,.038),rough=.93)
    ridge=material('DeadBarkRidges',(.105,.048,.017),rough=.97)
    wood=material('BrokenHeartwood',(.28,.15,.067),rough=.95)
    # Hollow broken crown, fluted irregular trunk and individually tapered
    # roots/boughs replace the reconstruction's hallucinated exterior planes.
    sides=24;vs=[];fs=[]
    rings=[(.0,.57),(.20,.43),(.48,.32),(.92,.25),(1.40,.22),(1.95,.20),(2.50,.22),(3.10,.23)]
    for j,(z,r) in enumerate(rings):
        for i in range(sides):
            a=i*math.tau/sides;flute=1+.12*math.sin(i*math.pi/2+.4)+.035*math.sin(j+i)
            top=.12*math.sin(i*2.1)+.06*math.sin(i*.7) if j==len(rings)-1 else 0
            vs.append((r*flute*math.cos(a)+.05*math.sin(j*.6),r*flute*math.sin(a),z+top))
    for j in range(len(rings)-1):
        for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
    for i in range(sides):
        a=i*math.tau/sides;vs.append((.15*math.cos(a)+.05*math.sin(4.2),.15*math.sin(a),3.10+.12*math.sin(i*2.1)+.06*math.sin(i*.7)))
    outer=(len(rings)-1)*sides;inner=len(rings)*sides
    for i in range(sides):fs.append((outer+i,outer+(i+1)%sides,inner+(i+1)%sides,inner+i))
    fs.append(tuple(reversed([inner+i for i in range(sides)])))
    trunk=mesh('HollowDeadTrunk',vs,fs,bark)
    for f in trunk.data.polygons:
        if f.center.z>3.0:f.use_smooth=False
    for i in range(9):
        a=i*math.tau/9+.12;r=1.03+.13*math.sin(i*2)
        tube('RootFlare',[(.12*math.cos(a),.12*math.sin(a),.42),(.46*math.cos(a),.46*math.sin(a),.19),(.80*math.cos(a),.80*math.sin(a),.08),(r*math.cos(a),r*math.sin(a),.015)],[.18,.14,.071,.003],bark,9)
    branches=[[(0,0,1.55),(-.48,.08,1.95),(-1.0,.14,2.15),(-1.37,.17,2.38)],[(.03,0,2.13),(.49,.08,2.40),(.93,.02,2.55),(1.28,-.05,2.67)],[(.02,.04,1.16),(.43,-.26,1.43),(.72,-.35,1.69)],[(.04,.04,2.65),(-.28,.32,2.89),(-.49,.51,3.12)],[(.03,0,2.68),(.26,-.30,2.94),(.40,-.46,3.19)]]
    for i,points in enumerate(branches):
        radii=[.15,.11,.065,.006] if len(points)==4 else [.13,.077,.005]
        tube('TaperedBough',points,radii,bark,12)
        for j in range(1,len(points)-1):
            p=Vector(points[j]);end=p+Vector(((-1 if i%2 else 1)*.17,.09,.31))
            tube('BareTwig',[p,p+(end-p)*.58,end],[.044,.023,.002],wood,7)
        for offset in [-.055,.055]:
            tube('BoughBarkRidge',[Vector(p)+Vector((0,offset,r*.78)) for p,r in zip(points,radii)],[max(.002,r*.10) for r in radii],ridge,5)
    for i in range(12):
        a=i*math.tau/12
        points=[(r*math.cos(a)+.05*math.sin(j*.6),r*math.sin(a),z) for j,(z,r) in enumerate(rings)]
        tube('VerticalBarkFlute',points,[.018,.018,.016,.013,.011,.01,.012,.005],ridge,5)
    collapse_colors('DeadTree')
    save('dead_tree','Full clean remodeling from four-view dead-tree reference: hollow splintered crown, fluted trunk, nine roots, five tapered boughs and forks. Native shell candidate rejected after angle review.')

def mesh(name,vertices,faces,mat,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    data.materials.append(mat)
    for p in data.polygons:p.use_smooth=smooth
    return obj

def tube(name,points,radius,mat,sides=5):
    vs=[];fs=[]
    x=Vector((1,0,0))
    for j,point in enumerate(points):
        center=Vector(point);t=(Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)])).normalized()
        # Parallel transport keeps successive rings aligned through straight
        # vertical segments and knee bends, avoiding pinched hourglass legs.
        x=x-t*x.dot(t)
        if x.length<.01:x=Vector((0,1,0))-t*t.y
        x.normalize();y=t.cross(x);r=radius[j] if isinstance(radius,list) else radius
        for i in range(sides):
            angle=i*math.tau/sides;vs.append(center+r*(x*math.cos(angle)+y*math.sin(angle)))
    for j in range(len(points)-1):
        for i in range(sides):a=j*sides+i;b=j*sides+(i+1)%sides;fs.append((a,b,b+sides,a+sides))
    fs.extend([tuple(reversed(range(sides))),tuple((len(points)-1)*sides+i for i in range(sides))])
    return mesh(name,vs,fs,mat)

def fern():
    bpy.ops.wm.read_factory_settings(use_empty=True);random.seed(2307)
    greens=[material('FernLeaf_'+str(i),color) for i,color in enumerate([(.055,.115,.018),(.095,.17,.030),(.15,.22,.045)])]
    stem=material('FernWeatheredStem',(.095,.051,.017));vein=material('FernMidrib',(.12,.20,.045))
    verts=[[] for _ in greens];faces=[[] for _ in greens]
    for frond in range(7):
        angle=frond*math.tau/7+.18
        direction=Vector((math.cos(angle),math.sin(angle),0));cross=Vector((-direction.y,direction.x,0))
        reach=.48+.13*math.sin(frond*2.3);height=.46+.18*math.cos(frond*1.9)
        def point(t):return direction*(reach*t**1.45)+Vector((0,0,.07+height*math.sin(t*math.pi*.70)))
        tube('FrondStem_'+str(frond),[point(j/8) for j in range(9)],[.006*(1-j/9) for j in range(9)],stem)
        for row in range(1,15):
            t=.10+row*.059;center=point(t)
            length=.22*math.sin(t*math.pi)**.75*(1-.28*t)
            for side in [-1,1]:
                axis=(cross*side+direction*.32+Vector((0,0,-.10*t))).normalized()
                tip=center+axis*length;across=(direction*.72+Vector((0,0,.69)))*(length*.28)
                mid=center+axis*length*.43+Vector((0,0,.011))
                color=(frond+row+(side>0))%3;base=len(verts[color])
                verts[color].extend([center,mid-across,mid+Vector((0,0,.008)),mid+across,tip])
                faces[color].extend([(base,base+1,base+2),(base,base+2,base+3),
                    (base+1,base+4,base+2),(base+2,base+4,base+3)])
        tube('GrowingTip_'+str(frond),[point(.89),point(.95),point(1)],.004,vein)
    for i in range(3):mesh('FernPairedLeaflets_'+str(i),verts[i],faces[i],greens[i])
    for i in range(9):
        a=i*2.4;tube('DryCrownStem_'+str(i),[(.03*math.cos(a),.03*math.sin(a),0),(.06*math.cos(a),.06*math.sin(a),.09)],.008,stem)
    # Merge three leaf colours and stems into one MultiMesh-friendly surface.
    objects=list(bpy.context.scene.objects);bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
    obj=bpy.context.object;colors=obj.data.color_attributes.new(name='PlantColor',type='FLOAT_COLOR',domain='CORNER')
    for polygon in obj.data.polygons:
        color=obj.data.materials[polygon.material_index].diffuse_color
        for loop in polygon.loop_indices:colors.data[loop].color=color
        polygon.material_index=0
    obj.data.materials.clear();combined=material('Fern-vcol',(1,1,1));obj.data.materials.append(combined)
    node=combined.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='PlantColor'
    combined.node_tree.links.new(node.outputs['Color'],combined.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    save('fern','Full foliage rebuild: seven fronds, 196 individual leaflets, curved midribs; front/top sheet authority.')

def collapse_colors(name):
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object
    o.name='Clean_'+name
    colors=o.data.color_attributes.new(name='SurfaceColor',type='FLOAT_COLOR',domain='CORNER')
    for f in o.data.polygons:
        color=o.data.materials[f.material_index].diffuse_color
        for loop in f.loop_indices:colors.data[loop].color=color
        f.material_index=0
    o.data.materials.clear();mat=material(name+'-vcol',(1,1,1));o.data.materials.append(mat)
    node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='SurfaceColor'
    mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    return o

def ellipsoid(name,point,radii,mat,segments=12,rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=point)
    o=bpy.context.object;o.name=name;o.scale=radii
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(mat)
    for f in o.data.polygons:f.use_smooth=True
    return o

def plank(name,point,size,mat,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=point)
    o=bpy.context.object;o.name=name;o.scale=size;o.rotation_euler=rotation
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.data.materials.append(mat)
    bevel=o.modifiers.new('WornEdge','BEVEL');bevel.width=min(size)*.08;bevel.segments=2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o

def town_prop(key):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    wood=material('TownTimber',(.15,.081,.032));pale=material('WornTimber',(.23,.135,.054))
    cloth=material('MarketCanvas',(.17,.22,.18));stone=material('WellSlate',(.19,.22,.20));iron=material('AnvilIron',(.08,.095,.10),.5,.55)
    if key=='market_stall':
        for side in [-1,1]:
            for y in [-.60,.60]:plank('JoineryPost',(side*1.45,y,1.28),(.13,.13,2.56),wood)
            plank('TopRail',(0,side*.61,2.52),(3.1,.13,.13),pale)
        for i in range(10):plank('CounterPlank',(-1.40+i*.31,0,1.10),(.30,.95,.08),pale if i%3 else wood)
        for side in [-1,1]:plank('CounterLeg',(side*1.24,.16,.52),(.15,.15,1.04),wood)
        for i in range(10):plank('CounterFacing',(-1.40+i*.31,-.48,.56),(.28,.045,1.0),wood)
        vs=[];fs=[]
        for y in range(9):
            for x in range(13):vs.append((-1.7+x/12*3.4,-.92+y/8*1.84,2.64-.18*abs((y-4)/4)+.035*math.sin(x*math.pi)))
        for y in range(8):
            for x in range(12):a=y*13+x;fs.append((a,a+1,a+14,a+13))
        mesh('TensionedCanvas',vs,fs,cloth)
        for i in range(13):plank('CanvasFringe',(-1.56+i*.26,-.94,2.34),(.20,.023,.19),cloth)
        for x in [-1.56,1.56]:tube('TieRope',[(x,-.92,2.5),(x,-.68,2.5),(x,-.62,2.28)],.006,pale,5)
    elif key=='well':
        for row in range(4):
            for i in range(16):
                a=(i+row*.5)*math.tau/16
                plank('MortaredStone',(.68*math.sin(a),.68*math.cos(a),.10+row*.19),(.27,.22,.18),stone,(0,0,-a))
        for x in [-.73,.73]:plank('WellPost',(x,0,1.33),(.14,.15,1.32),wood)
        tube('Axle',[(-.90,0,1.92),(.90,0,1.92)],.055,pale,12)
        tube('HangingRope',[(0,0,1.92),(0,0,.46)],.009,pale,6)
        for side in [-1,1]:plank('WeatherRoof',(side*.42,0,2.12),(.92,1.75,.07),wood,(0,side*.34,0))
    elif key=='fence':
        for y in [-1.0,1.0]:plank('FencePost',(0,y,.65),(.15,.15,1.3),wood)
        for z in [.47,.90]:plank('FenceRail',(0,0,z),(.09,2.14,.10),pale)
    elif key=='gate':
        for x in [-2.5,2.5]:plank('GatePillar',(x,0,1.65),(.40,.40,3.3),wood)
        plank('GateLintel',(0,0,3.26),(5.65,.43,.28),wood)
        for side in [-1,1]:tube('GateBrace',[(side*2.45,0,2.62),(side*1.82,0,3.22)],.067,pale,8)
        for x in [-2.57,2.57]:plank('PillarFoot',(x,0,.12),(.53,.53,.24),stone)
    elif key=='anvil':
        plank('Stump',(0,0,.34),(.60,.55,.68),wood)
        plank('AnvilFoot',(0,0,.72),(.65,.42,.12),iron)
        plank('AnvilWaist',(0,0,.82),(.24,.22,.18),iron)
        plank('WorkingFace',(0,0,.96),(.68,.32,.14),iron)
        tube('AnvilHorn',[(.27,0,.96),(.47,0,.96),(.62,0,.98)],[.11,.065,.001],iron,10)
    else:raise ValueError(key)
    collapse_colors(key.title());save(key,'New crafted town prop from Briarwood architecture palette: beveled joinery, planks, supports and separate functional surfaces.')

def bridge():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    wood=material('BridgeTimber',(.14,.077,.030));light=material('BridgeWeatheredPlanks',(.22,.13,.052));rope=material('BridgeHemp',(.33,.26,.15))
    for side in [-1,1]:
        plank('ContinuousDeckBeam',(side*.78,0,.11),(.16,6.20,.21),wood)
        for y in [-2.85,0,2.85]:
            plank('RailingPost',(side*1.02,y,.79),(.17,.18,1.58),wood)
            plank('PostFoot',(side*1.02,y,.10),(.28,.27,.20),wood)
            for z in [1.12,1.48]:
                tube('PostBinding',[(side*1.02+.108*math.sin(i*math.tau/16),y+.108*math.cos(i*math.tau/16),z) for i in range(17)],.009,rope,5)
        for z in [.79,1.36]:
            for span in [-1,1]:
                path=[(side*1.02,span*t*2.85,z-.10*math.sin(t*math.pi)) for t in [i/12 for i in range(13)]]
                tube('ContinuousHempRail',path,.020,rope,8)
    for i in range(28):
        y=-3.04+i*.225
        plank('DeckBoard',(0,y,.25), (2.0,.216,.095),light if i%3 else wood,(0,.006*math.sin(i*2.4),0))
        for side in [-1,1]:ellipsoid('WoodenPeg',(side*.79,y,.302),(.013,.013,.005),wood,6,3)
    collapse_colors('Bridge')
    save('bridge','Native reconstruction duplicated detached corner posts and broke the rails. Complete clean deck, exactly six railing posts, closed beams, planks, bindings and two continuous ropes per side rebuilt from the four-view bridge sheet.')

def leaf_litter():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng=random.Random(13904)
    mats=[material('DryOak',(.26,.12,.038)),material('OldLeaf',(.15,.068,.024)),material('AmberLeaf',(.34,.20,.057))]
    for i in range(56):
        center=Vector((rng.uniform(-.75,.75),rng.uniform(-.52,.52),rng.uniform(.002,.018)))
        angle=rng.uniform(0,math.tau);length=rng.uniform(.07,.15);width=length*.48
        along=Vector((math.cos(angle),math.sin(angle),0));across=Vector((-math.sin(angle),math.cos(angle),0))
        points=[center-along*length,center-along*length*.36+across*width,center+along*length*.45+across*width*.75,
                center+along*length,center+along*length*.45-across*width*.75,center-along*length*.36-across*width,
                center+Vector((0,0,rng.uniform(.012,.025)))]
        mesh('FallenLeaf',points,[(j,(j+1)%6,6) for j in range(6)],mats[i%3],False)
    collapse_colors('LeafLitter')
    save('leaf_litter','Separate curled fallen leaves scattered across the ground, following the Briarwood forest-floor concept; grass-shaped candidate rejected.')

def grass():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng=random.Random(23811)
    mats=[material('GrassGreen',(.13,.21,.036)),material('GrassLight',(.19,.27,.064)),material('DryTips',(.32,.28,.097))]
    for tuft in range(7):
        center=Vector((math.sin(tuft*2.4)*.14,math.cos(tuft*2.4)*.14,.006))
        for blade in range(12):
            a=blade*2.4+tuft*.41;direction=Vector((math.sin(a),math.cos(a),0));across=Vector((math.cos(a),-math.sin(a),0))
            height=rng.uniform(.26,.47);reach=rng.uniform(.10,.31);vs=[];fs=[]
            for row in range(7):
                t=row/6;point=center+direction*(reach*t*t)+Vector((0,0,height*math.sin(t*1.70)))
                width=.018*(math.sin(math.pi*t*.88)*.65+.35)*(1-t)+.00015
                vs.extend([point-across*width,point+Vector((0,0,.0025*(1-t))),point+across*width])
                if row:
                    j=(row-1)*3;fs.extend([(j,j+3,j+4,j+1),(j+1,j+4,j+5,j+2)])
            o=mesh('ArchedBlade',vs,fs,mats[(blade+tuft)%2]);o.data.materials.append(mats[2])
            for f in o.data.polygons:
                if f.index>=10:f.material_index=1
    collapse_colors('Grass')
    save('grass','Thin foliage rebuilt: seven tufts, 84 arched folded blades; native fused leaves rejected at 4,000 triangles.')

def small_prop(key):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    wood=material('AgedWood',(.12,.067,.025));green=material('LeafGreen',(.08,.16,.04))
    linen=material('Linen',(.36,.30,.18));bone=material('BoneIvory',(.45,.42,.31));red=material('RedOchre',(.20,.046,.027))
    if key in ['flowers','mushroom']:
        for i in range(5 if key=='flowers' else 3):
            a=i*2.4;x=math.sin(a)*.19;y=math.cos(a)*.17;h=.24+(i%3)*.055
            tube('Stem',[(x,y,0),(x+.012,y,h)],.009 if key=='flowers' else .022,green if key=='flowers' else linen,6)
            if key=='flowers':
                for j in range(6):
                    a=j*math.tau/6;ellipsoid('Petal',(x+math.sin(a)*.037,y+math.cos(a)*.037,h),(.030,.022,.014),linen,8,4)
                ellipsoid('Pollen',(x,y,h+.014),(.013,.013,.01),red,8,4)
                for side in [-1,1]:mesh('Leaf',[(x,y,h*.6),(x+side*.075,y+.02,h*.73),(x+side*.105,y,h*.75),(x+side*.05,y-.02,h*.68)],[(0,1,2,3)],green)
            else:
                vs=[];fs=[];n=16
                for r,z in [(0,h+.095),(.050,h+.080),(.093,h+.040),(.105,h),(.075,h-.015),(0,h-.005)]:
                    for j in range(n):a=j*math.tau/n;vs.append((x+r*math.sin(a),y+r*math.cos(a),z))
                for row in range(5):
                    for j in range(n):v=row*n+j;w=row*n+(j+1)%n;fs.append((v,w,w+n,v+n))
                mesh('FlaredCap',vs,fs,red)
                for j in range(5):a=j*2.4;ellipsoid('CapSpot',(x+math.sin(a)*.055,y+math.cos(a)*.055,h+.06),(.009,.012,.004),linen,6,3)
    elif key=='eggs':
        for i in range(4):
            x=(i%2)*.18-.09;y=(i//2)*.17-.085;h=.15+(i%2)*.025
            ellipsoid('SilkEggSac',(x,y,h),(.10,.09,h),linen)
            for j in range(3):tube('SilkWrap',[(x+.10*math.sin(t*math.tau/16),y+.09*math.cos(t*math.tau/16),h+(j-1)*.065) for t in range(17)],.0035,bone,4)
    elif key=='bones':
        tube('Spine',[(-.45,0,.035),(0,.04,.08),(.47,0,.045)],[.024,.033,.017],bone,8)
        for i in range(6):
            x=-.30+i*.12
            for side in [-1,1]:tube('CurvedRib',[(x,0,.075),(x,side*.12,.23),(x+.02,side*.26,.16),(x+.06,side*.30,.02)],[.014,.016,.011,.005],bone,6)
        ellipsoid('Skull',(.53,0,.06),(.11,.085,.065),bone)
    elif key in ['web','banner']:
        for side in [-1,1]:tube('Stake',[(side*.85,0,0),(side*.83,0,2.15)],[.055,.040],wood,8)
        if key=='web':
            for i in range(12):
                a=i*math.tau/12;tube('RadialSilk',[(0,0,1.17),(.83*math.sin(a),0,1.17+.80*math.cos(a))],.003,linen,4)
                for r in [.22,.43,.64,.80]:tube('SpiralSilk',[(r*math.sin(a),0,1.17+r*math.cos(a)),(r*math.sin(a+math.tau/12),0,1.17+r*math.cos(a+math.tau/12))],.0025,linen,4)
        else:
            tube('Crossbar',[(-.9,0,2.05),(.9,0,2.05)],.035,wood,8)
            vs=[];fs=[]
            for z in range(6):
                for x in range(13):vs.append((-.80+x/12*1.6,.042*math.sin(x*.8+z*.4),2.00-z*.19-(.055 if z==5 and x%2 else 0)))
            for z in range(5):
                for x in range(12):a=z*13+x;fs.append((a,a+1,a+14,a+13))
            mesh('FoldedCloth',vs,fs,red)
    elif key=='pouch':
        hide=material('PouchLeather',(.15,.068,.019),rough=.92)
        ellipsoid('ClosedLeatherBundle',(0,0,.078),(.105,.088,.076),hide,16,8)
        tube('GatheredNeck',[(0,0,.11),(0,0,.17)],[.047,.025],hide,12)
        tube('Drawstring',[(.030*math.sin(i*math.tau/16),.030*math.cos(i*math.tau/16),.15) for i in range(17)],.003,linen,5)
        tube('HangingCord',[(.02,-.015,.15),(.064,-.016,.12),(.042,-.02,.055)],.003,linen,5)
    elif key=='fire':
        ember=material('CoalGlow',(.46,.09,.009));p=ember.node_tree.nodes['Principled BSDF'];p.inputs['Emission Color'].default_value=(.60,.09,.005,1);p.inputs['Emission Strength'].default_value=1.8
        for i in range(6):
            a=i*math.tau/6;tube('CharredLog',[(math.sin(a)*.40,math.cos(a)*.40,.055),(-math.sin(a)*.16,-math.cos(a)*.16,.13)],[.065,.045],wood,8)
            ellipsoid('Coal',(math.sin(a)*.09,math.cos(a)*.09,.07),(.065,.055,.028),ember,8,4)
        # Retain separate emissive coal surface; the existing particle system
        # supplies motion, instead of baking orange solid cones into the mesh.
    else:raise ValueError(key)
    if key!='fire':collapse_colors(key.title())
    save(key,'New clean prop sections following the Briarwood ground-dressing palette; no legacy mesh reuse.')

def save(key,repair):
    bpy.context.preferences.filepaths.save_version=0
    target=ROOT/'blender/multiview_rebuild/prepared'/f'{key}.blend';target.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    runtime=ROOT/'game/review_assets/full_rebuild'/key/'runtime.glb';runtime.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(runtime),export_format='GLB',export_animations=False,export_skins=False)
    triangles=sum(len(p.vertices)-2 for o in bpy.context.scene.objects if o.type=='MESH' for p in o.data.polygons)
    (ROOT/'docs/full_asset_rebuild'/f'{key}_repair.json').write_text(json.dumps({
        'key':key,'method':'clean_remodel','repair':repair,'triangles':triangles,
        'reference':f'concepts_docs/art/asset_turnarounds_v2/{key}/turnaround.png' if key in ['fern','grass'] else 'concepts_docs/art/world_briarwood.png',
        'old_geometry_reused':False,'review_status':'pending_exported_review'},indent=2))
    print('CLEAN_REBUILD',key,triangles,flush=True)

if __name__=='__main__':
    for key in sys.argv[sys.argv.index('--')+1:]:
        if key=='fern':fern()
        elif key=='grass':grass()
        elif key=='leaf_litter':leaf_litter()
        elif key in ['flowers','mushroom','eggs','bones','web','banner','pouch','fire']:small_prop(key)
        elif key in ['market_stall','well','fence','gate','anvil']:town_prop(key)
        elif key=='bridge':bridge()
        elif key=='dead_tree':dead_tree()
        else:raise ValueError(key)
