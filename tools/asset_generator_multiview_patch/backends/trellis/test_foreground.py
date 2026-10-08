import numpy as np
from PIL import Image,ImageDraw
from foreground import studio_foreground

def test_foliage_and_enclosed_white_are_preserved():
    im=Image.new('RGB',(128,128),'#f5f5f5');d=ImageDraw.Draw(im)
    d.rectangle((50,35,77,115),fill='#684d39')
    d.rectangle((57,50,69,65),fill='#ffffff')
    d.line((10,20,65,50,118,10),fill='#526c38',width=2)
    masked,method=studio_foreground(im)
    alpha=np.asarray(masked)[:,:,3]
    assert method=='neutral_border_flood_fill'
    assert alpha[0,0]==0 and alpha[20,10]==255 and alpha[55,60]==255

def test_complex_background_uses_semantic_mask():
    im=Image.new('RGB',(128,128),'#3683ab')
    assert studio_foreground(im)[0] is None

def test_existing_alpha_is_authoritative():
    im=Image.new('RGBA',(128,128),(1,2,3,0))
    assert studio_foreground(im)[1]=='provided_alpha'
